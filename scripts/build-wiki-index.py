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


def clean_content(text, max_len=800):
    """Strip markdown markup, truncate."""
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
    return text[:max_len]


def build_index(vault_dir):
    wiki_dir = os.path.join(vault_dir, "wiki")
    entries = []

    if not os.path.isdir(wiki_dir):
        print(f"Wiki dir not found: {wiki_dir}", file=sys.stderr)
        return entries

    for subdir in ["entities", "concepts", "sources", "synthesis"]:
        path = os.path.join(wiki_dir, subdir)
        if not os.path.isdir(path):
            continue
        for fname in sorted(os.listdir(path)):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(path, fname)
            with open(filepath, encoding="utf-8") as f:
                raw = f.read()

            fm, body = parse_frontmatter(raw)
            if len(body) < 20:
                continue

            name = fm.get("name", fm.get("title", fname.replace(".md", "")))
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            entry = {
                "id": f"{subdir}/{fname.replace('.md', '')}",
                "type": fm.get("type", subdir.rstrip("s")),
                "name": str(name),
                "category": fm.get("category", ""),
                "tags": tags,
                "content": clean_content(body),
                "first_seen": fm.get("first_seen", ""),
                "last_updated": fm.get("last_updated", ""),
                "source_type": fm.get("source_type", ""),
            }
            entries.append(entry)

    return entries


def main():
    parser = argparse.ArgumentParser(description="Build wiki search index")
    parser.add_argument("vault_dir", nargs="?", default="vault-content")
    parser.add_argument("-o", "--output", default="worker/wiki-data.json")
    args = parser.parse_args()

    entries = build_index(args.vault_dir)
    print(f"Indexed {len(entries)} wiki pages from {args.vault_dir}/wiki/")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(args.output) / 1024
    print(f"Written {args.output} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
