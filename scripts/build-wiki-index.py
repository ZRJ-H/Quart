#!/usr/bin/env python3
"""Extract Obsidian wiki + daily content into a searchable JSON index.

Zero dependencies - uses only Python stdlib.
"""

import argparse
import json
import os
import re
import sys


def _strip_emoji(text):
    """Remove emoji/special chars, keep CJK, ASCII word chars, slash."""
    return re.sub(r"[^一-鿿a-zA-Z0-9/\s_-]", "", text).strip()


# Config keys:
#   use_denylist (bool)  – True: include all H2 except those in 'exclude' / 'exclude_if_contains'
#                          False: include only H2 in 'allow'
#   allow (set)          – allowlist mode: exact match after emoji strip
#   exclude (set)        – denylist mode: exact match after emoji strip
#   exclude_if_contains  – denylist mode: substring match against raw H2 title
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
    "GitHub Trending": {
        "category": "github-trending",
        "use_denylist": True,
        "exclude": {
            "今日概览", "今日速览", "今日增量", "数据说明", "数据质量说明",
            "补充数据", "统计", "趋势观察", "连续在榜项目",
            "项目进出榜追踪", "常驻观察", "与其他线的关联", "重大数据源发现",
        },
        "exclude_if_contains": [],
    },
    "Hacker News": {
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
    """Parse simple YAML-like frontmatter without external libraries."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm_text = parts[1]
    body = parts[2].strip()

    data = {}
    current_list = None

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


def clean_content(text, max_len=800, summary_len=30):
    """Strip markdown markup, truncate to full and summary lengths."""
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
    """Extract (title, content) pairs for H3 blocks under eligible H2 sections."""
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


def build_daily_index(vault_dir):
    """Build article-level index entries from daily content directories."""
    light_entries = []
    full_entries = []

    for dir_name, config in DAILY_DIRS.items():
        dir_path = os.path.join(vault_dir, dir_name)
        if not os.path.isdir(dir_path):
            print(f"Daily dir not found: {dir_path}", file=sys.stderr)
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
            with open(filepath, encoding="utf-8", errors="replace") as f:
                raw = f.read()

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
            source_file = f"{dir_name}/{date_str}"

            for title_raw, content_text in articles:
                # Clean title: strip markdown links, bold, emoji
                title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title_raw)
                title = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", title).strip()
                full_content, summary = clean_content(content_text)
                entry_id = f"daily/{dir_name}/{date_str}#{slugify_title(title)}"

                light_entries.append({
                    "id": entry_id,
                    "name": title,
                    "type": "daily",
                    "category": category,
                    "tags": tags,
                    "last_updated": date_str,
                    "summary": summary,
                    "reference_count": 0,
                })
                full_entries.append({
                    "id": entry_id,
                    "name": title,
                    "type": "daily",
                    "category": category,
                    "tags": tags,
                    "content": full_content,
                    "first_seen": date_str,
                    "last_updated": date_str,
                    "source_type": "daily",
                    "source_file": source_file,
                    "reference_count": 0,
                })
                article_count += 1

        print(f"  {dir_name}: {file_count} files, {article_count} articles")

    return light_entries, full_entries


def build_index(vault_dir):
    wiki_dir = os.path.join(vault_dir, "wiki")
    light_entries = []
    full_entries = []

    if not os.path.isdir(wiki_dir):
        print(f"Wiki dir not found: {wiki_dir}", file=sys.stderr)
        return light_entries, full_entries

    link_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
    link_counter = {}
    staged = []

    for subdir in ["entities", "concepts", "sources", "synthesis"]:
        path = os.path.join(wiki_dir, subdir)
        if not os.path.isdir(path):
            continue
        for fname in sorted(os.listdir(path)):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(path, fname)
            with open(filepath, encoding="utf-8", errors="replace") as f:
                raw = f.read()

            fm, body = parse_frontmatter(raw)
            if len(body) < 20:
                continue

            for target in link_re.findall(body):
                t = target.strip()
                if t:
                    link_counter[t] = link_counter.get(t, 0) + 1

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
            source_type = fm.get("source_type", "")

            full_content, summary = clean_content(body)

            light_entry = {
                "id": entry_id,
                "name": str(name),
                "type": entry_type,
                "category": category,
                "tags": tags,
                "last_updated": last_updated,
                "summary": summary,
            }
            full_entry = {
                "id": entry_id,
                "type": entry_type,
                "name": str(name),
                "category": category,
                "tags": tags,
                "content": full_content,
                "first_seen": first_seen,
                "last_updated": last_updated,
                "source_type": source_type,
            }
            staged.append((light_entry, full_entry, str(name)))

    for light_entry, full_entry, name in staged:
        rc = link_counter.get(name, 0)
        light_entry["reference_count"] = rc
        full_entry["reference_count"] = rc
        light_entries.append(light_entry)
        full_entries.append(full_entry)

    return light_entries, full_entries


def main():
    parser = argparse.ArgumentParser(description="Build wiki search index")
    parser.add_argument("vault_dir", nargs="?", default="vault-content")
    parser.add_argument("-o", "--output", default="worker/wiki-data.json")
    parser.add_argument("--light-output", default="worker/wiki-index-light.json")
    parser.add_argument("--full-output", default="worker/wiki-data-full.json")
    args = parser.parse_args()

    light_entries, full_entries = build_index(args.vault_dir)
    print(f"Indexed {len(full_entries)} wiki pages from {args.vault_dir}/wiki/")

    print("Indexing daily content...")
    daily_light, daily_full = build_daily_index(args.vault_dir)
    print(f"Indexed {len(daily_full)} daily articles total")
    light_entries.extend(daily_light)
    full_entries.extend(daily_full)

    print(f"Total entries: {len(full_entries)}")

    os.makedirs(os.path.dirname(args.light_output) or ".", exist_ok=True)

    with open(args.light_output, "w", encoding="utf-8") as f:
        json.dump(light_entries, f, ensure_ascii=False, separators=(",", ":"))
    light_kb = os.path.getsize(args.light_output) / 1024
    print(f"Light index: {len(light_entries)} entries, {light_kb:.1f} KB")

    with open(args.full_output, "w", encoding="utf-8") as f:
        json.dump(full_entries, f, ensure_ascii=False, separators=(",", ":"))
    full_kb = os.path.getsize(args.full_output) / 1024
    print(f"Full index: {len(full_entries)} entries, {full_kb:.1f} KB")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(light_entries, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(args.output) / 1024
    print(f"Legacy output: {args.output} ({size_kb:.1f} KB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
