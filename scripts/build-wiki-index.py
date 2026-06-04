#!/usr/bin/env python3
"""Extract Obsidian wiki content into a searchable JSON index.

Zero dependencies - uses only Python stdlib.
"""

import argparse
import json
import os
import re
import sys


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

        # list items under a key (tags: [...])
        if current_list:
            m = re.match(r"^\s*-\s+(.+)$", line)
            if m:
                current_list.append(m.group(1).strip().strip('"').strip("'"))
                continue
            else:
                data[current_key] = current_list
                current_list = None
                current_key = None

        # key: value
        m = re.match(r"^(\w[\w_-]*)\s*:\s*(.+)$", line)
        if not m:
            continue

        key = m.group(1)
        val = m.group(2).strip()

        # list start: [...]
        if val == "[" or val.startswith("["):
            current_list = []
            current_key = key
            # inline list [a, b]
            list_match = re.match(r"^\[(.*)\]$", val)
            if list_match:
                items = re.findall(r"'([^']*)'|\"([^\"]*)\"|([^,\s]+)", list_match.group(1))
                current_list = [i[0] or i[1] or i[2] for i in items if any(i)]
                data[key] = current_list
                current_list = None
                current_key = None
            continue

        # quoted string
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            data[key] = val[1:-1]
        else:
            data[key] = val

    if current_list and current_key:
        data[current_key] = current_list

    return data, body


def clean_content(text, max_len=800, summary_len=30):
    """Strip markdown markup, truncate to full and summary lengths."""
    # wikilinks: [[page]] or [[page|alias]]
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"\1", text)
    # markdown links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # headers
    text = re.sub(r"#{1,6}\s*", "", text)
    # bold/italic
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    # inline code
    text = re.sub(r"`{1,3}[^`]+`{1,3}", "", text)
    # table rows
    text = re.sub(r"\|[^|]+\|", " ", text)
    # horizontal rules and excess newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("---", " ")
    text = text.strip()
    return text[:max_len], text[:summary_len]


def build_index(vault_dir):
    wiki_dir = os.path.join(vault_dir, "wiki")
    light_entries = []
    full_entries = []

    if not os.path.isdir(wiki_dir):
        print(f"Wiki dir not found: {wiki_dir}", file=sys.stderr)
        return light_entries, full_entries

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

            name = fm.get("name", fm.get("title", fname.replace(".md", "")))
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            entry_id = f"{subdir}/{fname.replace('.md', '')}"
            entry_type = fm.get("type", subdir.rstrip("s"))
            category = fm.get("category", "")
            first_seen = fm.get("first_seen", "")
            last_updated = fm.get("last_updated", "")
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
            light_entries.append(light_entry)

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

    os.makedirs(os.path.dirname(args.light_output) or ".", exist_ok=True)

    with open(args.light_output, "w", encoding="utf-8") as f:
        json.dump(light_entries, f, ensure_ascii=False, separators=(",", ":"))
    light_kb = os.path.getsize(args.light_output) / 1024
    print(f"Light index: {len(light_entries)} pages, {light_kb:.1f} KB")

    with open(args.full_output, "w", encoding="utf-8") as f:
        json.dump(full_entries, f, ensure_ascii=False, separators=(",", ":"))
    full_kb = os.path.getsize(args.full_output) / 1024
    print(f"Full index: {len(full_entries)} pages, {full_kb:.1f} KB")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(light_entries, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(args.output) / 1024
    print(f"Legacy output: {args.output} ({size_kb:.1f} KB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
