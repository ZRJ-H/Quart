#!/usr/bin/env python3
"""把 wiki-data-full.json 过滤为「仅 changed-ids.json 中的条目」，用于增量嵌入。

Usage: filter-changed.py <full.json> <changed-ids.json> <out.json>
将子集写入 out.json，并把条目数打印到 stdout（供 shell 判断是否跳过）。
"""
import json
import os
import sys


def main():
    full_path, changed_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    changed = set()
    if os.path.exists(changed_path):
        with open(changed_path, encoding="utf-8") as f:
            changed = set(json.load(f))
    with open(full_path, encoding="utf-8") as f:
        data = json.load(f)
    subset = [e for e in data if e.get("id") in changed]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(subset, f, ensure_ascii=False)
    print(len(subset))


if __name__ == "__main__":
    main()
