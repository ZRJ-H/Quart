#!/usr/bin/env python3
"""从 content/ 解析 Markdown 文件 → 写入 SQLite wiki.db（FTS5 全文索引）

Zero dependencies - uses only Python stdlib (sqlite3).
"""

import argparse
import json
import os
import re
import sqlite3
import sys


def _strip_emoji(text):
    return re.sub(r"[^一-鿿a-zA-Z0-9/\s_-]", "", text).strip()


DAILY_DIRS = {
    "AI科技动态": {
        "category": "ai-news",
        "use_denylist": True,
        "exclude": {
            "今日概览", "趋势观察", "信息来源说明", "与其他线的关联",
            "今日关键词", "近期重要事件预告", "今日日历",
        },
        "exclude_if_contains": ["GitHub AI", "arXiv"],
    },
    "时政要闻": {
        "category": "daily-news",
        "use_denylist": True,
        "exclude": {
            "今日概览", "信息来源说明", "趋势观察", "今日日历",
            "与其他线的关联", "今日关键词",
        },
        "exclude_if_contains": [],
    },
    "GitHub-Trending": {
        "category": "github-trending",
        "use_denylist": True,
        "exclude": {
            "今日概览", "今日速览", "今日增量", "数据说明", "数据质量说明",
            "补充数据", "统计", "趋势观察", "连续在榜项目",
            "项目进出榜追踪", "常驻观察", "与其他线的关联", "重大数据源发现",
        },
        "exclude_if_contains": [],
    },
    "Hacker-News": {
        "category": "hn-daily",
        "use_denylist": False,
        "allow": {"今日精选"},
    },
    "AI论文日报": {
        "category": "arxiv-daily",
        "use_denylist": False,
        "allow": {"今日精选"},
    },
}


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    body = parts[2].strip()
    data = {}
    current_list = None
    current_key = None
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if current_list:
            m = re.match(r"^\s*-\s+(.+)$", line)
            if m:
                current_list.append(m.group(1).strip().strip('"').strip("'"))
                continue
            else:
                data[current_key] = current_list
                current_list = None
                current_key = None
        m = re.match(r"^(\w[\w_-]*)\s*:\s*(.+)$", line)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip()
        if val == "[" or val.startswith("["):
            current_list = []
            current_key = key
            list_match = re.match(r"^\[(.*)\]$", val)
            if list_match:
                items = re.findall(r"'([^']*)'|\"([^\"]*)\"|([^,\s]+)", list_match.group(1))
                current_list = [i[0] or i[1] or i[2] for i in items if any(i)]
                data[key] = current_list
                current_list = None
                current_key = None
            continue
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            data[key] = val[1:-1]
        else:
            data[key] = val
    if current_list and current_key:
        data[current_key] = current_list
    return data, body


def clean_content(text, max_len=1200, summary_len=200):
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"`{1,3}[^`]+`{1,3}", "", text)
    text = re.sub(r"\|[^|]+\|", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("---", " ")
    text = text.strip()
    return text[:max_len], text[:summary_len]


def parse_h3_blocks(body, config):
    use_denylist = config.get("use_denylist", False)
    allow = config.get("allow", set())
    exclude = config.get("exclude", set())
    exclude_if_contains = config.get("exclude_if_contains", [])

    articles = []
    current_h2_allowed = False
    current_h3_title = None
    current_lines = []

    for line in body.split("\n"):
        if line.startswith("## "):
            if current_h3_title and current_h2_allowed:
                articles.append((current_h3_title, "\n".join(current_lines)))
            current_h3_title = None
            current_lines = []

            h2_raw = line[3:].strip()
            h2 = _strip_emoji(h2_raw)

            if use_denylist:
                in_exclude = h2 in exclude or any(k in h2_raw for k in exclude_if_contains)
                current_h2_allowed = not in_exclude and bool(h2)
            else:
                current_h2_allowed = h2 in allow

        elif line.startswith("### ") and current_h2_allowed:
            if current_h3_title:
                articles.append((current_h3_title, "\n".join(current_lines)))
            current_h3_title = line[4:].strip()
            current_lines = []
        elif current_h3_title and current_h2_allowed:
            current_lines.append(line)

    if current_h3_title and current_h2_allowed:
        articles.append((current_h3_title, "\n".join(current_lines)))

    return articles


def slugify_title(text):
    slug = re.sub(r"[^一-鿿a-zA-Z0-9]", "-", text.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60]


def extract_links(text):
    """Extract unique wikilink targets before Markdown cleanup removes them."""
    link_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
    return list(dict.fromkeys(target.strip() for target in link_re.findall(text) if target.strip()))


def collect_daily_entries(vault_dir):
    """Parse daily Markdown files into portable search entry dictionaries."""
    entries = []

    for dir_name, config in DAILY_DIRS.items():
        dir_path = os.path.join(vault_dir, dir_name)
        if not os.path.isdir(dir_path):
            print(f"  SKIP: {dir_path} (not found)")
            continue

        category = config["category"]
        file_count = 0
        article_count = 0

        for fname in sorted(os.listdir(dir_path)):
            if not fname.endswith(".md"):
                continue
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
            if not date_match:
                continue
            date_str = date_match.group(1)

            filepath = os.path.join(dir_path, fname)
            try:
                with open(filepath, encoding="utf-8", errors="replace") as f:
                    raw = f.read()
            except Exception as e:
                print(f"  WARN: cannot read {filepath}: {e}", file=sys.stderr)
                continue

            fm, body = parse_frontmatter(raw)
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            if date_str not in tags:
                tags = list(tags) + [date_str]

            articles = parse_h3_blocks(body, config)
            if not articles:
                continue

            file_count += 1

            for title_raw, content_text in articles:
                title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title_raw)
                title = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", title).strip()
                full_content, summary = clean_content(content_text)
                entry_id = f"daily/{dir_name}/{date_str}#{slugify_title(title)}"

                entries.append({
                    "id": entry_id,
                    "name": title,
                    "type": "daily",
                    "category": category,
                    "tags": tags,
                    "summary": summary,
                    "content": full_content,
                    "last_updated": date_str,
                    "content_length": len(full_content),
                    "reference_count": 0,
                    "links": extract_links(content_text),
                    "page_path": f"{dir_name}/{date_str}",
                })
                article_count += 1

        print(f"  {dir_name}: {file_count} files, {article_count} articles")

    return entries


def collect_wiki_entries(vault_dir):
    """Parse private wiki records into portable search entry dictionaries."""
    wiki_dir = os.path.join(vault_dir, "wiki")
    if not os.path.isdir(wiki_dir):
        print(f"Wiki dir not found: {wiki_dir}")
        return []

    staged = []

    for subdir in ["entities", "concepts", "sources", "synthesis"]:
        path = os.path.join(wiki_dir, subdir)
        if not os.path.isdir(path):
            continue
        for fname in sorted(os.listdir(path)):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(path, fname)
            try:
                with open(filepath, encoding="utf-8", errors="replace") as f:
                    raw = f.read()
            except Exception as e:
                print(f"  WARN: cannot read {filepath}: {e}", file=sys.stderr)
                continue

            fm, body = parse_frontmatter(raw)
            if len(body) < 20:
                continue

            name = fm.get("name", fm.get("title", fname.replace(".md", "")))
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            entry_id = f"{subdir}/{fname.replace('.md', '')}"
            entry_type = fm.get("type", subdir.rstrip("s"))
            category = fm.get("category", "") or entry_type
            first_seen = fm.get("first_seen", "")
            last_updated = fm.get("last_updated", "") or first_seen
            if not last_updated:
                date_match = re.search(r"\d{4}-\d{2}-\d{2}", fname)
                if date_match:
                    last_updated = date_match.group(0)

            full_content, summary = clean_content(body)

            staged.append({
                "id": entry_id, "name": str(name), "type": entry_type,
                "category": category, "tags": tags, "summary": summary,
                "content": full_content, "last_updated": last_updated,
                "content_length": len(full_content),
                "reference_count": 0,
                "links": extract_links(body),
                "page_path": None,
            })

    return staged


def collect_entries(vault_dir):
    """Collect every searchable wiki and daily entry with link metadata."""
    entries = collect_wiki_entries(vault_dir) + collect_daily_entries(vault_dir)
    link_counter = {}
    for entry in entries:
        for target in entry.get("links", []):
            link_counter[target] = link_counter.get(target, 0) + 1
    for entry in entries:
        entry["reference_count"] = link_counter.get(entry["name"], 0)
    return entries


def write_entries_to_db(conn, entries):
    """Replace SQLite entries with a previously collected portable index."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries")
    for entry in entries:
        cursor.execute("""
            INSERT OR REPLACE INTO entries
            (id, name, type, category, tags, summary, content,
             last_updated, content_length, reference_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["id"], entry["name"], entry["type"], entry["category"],
            json.dumps(entry["tags"], ensure_ascii=False),
            entry["summary"], entry["content"],
            entry["last_updated"], entry["content_length"],
            entry["reference_count"],
        ))


def atomic_write_json(path, payload):
    """Write JSON through a sibling temporary file and atomically replace it."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    temp_path = f"{path}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def write_json_indexes(entries, full_path, light_path):
    """Write full Worker data and a smaller browser suggestion index."""
    atomic_write_json(full_path, entries)
    light_fields = (
        "id", "name", "type", "category", "tags", "summary",
        "last_updated", "reference_count", "links", "page_path",
    )
    light_entries = [
        {key: entry.get(key) for key in light_fields}
        for entry in entries
    ]
    atomic_write_json(light_path, light_entries)


def init_db(db_path):
    """创建 SQLite 数据库和 FTS5 表"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            type        TEXT DEFAULT '',
            category    TEXT DEFAULT '',
            tags        TEXT DEFAULT '[]',
            summary     TEXT DEFAULT '',
            content     TEXT DEFAULT '',
            last_updated TEXT DEFAULT '',
            content_length INTEGER DEFAULT 0,
            reference_count INTEGER DEFAULT 0
        );

        -- FTS5 全文索引（内容表）
        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            name,
            summary,
            content,
            tags,
            category,
            content=entries,
            content_rowid=rowid,
            tokenize='unicode61'
        );

        -- FTS5 同步触发器
        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, name, summary, content, tags, category)
            VALUES (new.rowid, new.name, new.summary, new.content, new.tags, new.category);
        END;
        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, name, summary, content, tags, category)
            VALUES ('delete', old.rowid, old.name, old.summary, old.content, old.tags, old.category);
        END;
        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, name, summary, content, tags, category)
            VALUES ('delete', old.rowid, old.name, old.summary, old.content, old.tags, old.category);
            INSERT INTO entries_fts(rowid, name, summary, content, tags, category)
            VALUES (new.rowid, new.name, new.summary, new.content, new.tags, new.category);
        END;
    """)

    return conn


def main():
    parser = argparse.ArgumentParser(description="Build wiki search indexes")
    parser.add_argument("vault_dir", nargs="?", default="content")
    parser.add_argument("-o", "--output", default="server/wiki.db",
                        help="SQLite database path (default: server/wiki.db)")
    parser.add_argument("--json-output",
                        help="Full JSON index path for the AI Worker")
    parser.add_argument("--light-output",
                        help="Light JSON index path for browser search")
    parser.add_argument("--no-sqlite", action="store_true",
                        help="Skip the compatibility SQLite index")
    args = parser.parse_args()

    vault_dir = args.vault_dir
    db_path = args.output
    if bool(args.json_output) != bool(args.light_output):
        parser.error("--json-output and --light-output must be used together")

    print("Collecting wiki and daily entries...")
    entries = collect_entries(vault_dir)
    wiki_count = sum(entry["type"] != "daily" for entry in entries)
    daily_count = len(entries) - wiki_count
    print(f"  Wiki pages: {wiki_count}")
    print(f"  Daily articles: {daily_count}")

    if not args.no_sqlite:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        conn = init_db(db_path)
        write_entries_to_db(conn, entries)
        conn.commit()
        fts_count = conn.execute("SELECT COUNT(*) FROM entries_fts").fetchone()[0]
        db_size = os.path.getsize(db_path) / 1024
        print(
            f"SQLite: {len(entries)} entries "
            f"({fts_count} FTS indexed), DB size: {db_size:.1f} KB"
        )
        conn.close()

    if args.json_output:
        write_json_indexes(entries, args.json_output, args.light_output)
        print(f"Full JSON: {args.json_output}")
        print(f"Light JSON: {args.light_output}")

    print(f"Total: {len(entries)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
