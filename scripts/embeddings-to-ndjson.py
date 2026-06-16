#!/usr/bin/env python3
"""把 embeddings.json ({id: vector}) 转换为 Vectorize 的 ndjson 格式。

Usage: embeddings-to-ndjson.py <embeddings.json> <out.ndjson>
"""
import json
import sys


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        embeddings = json.load(f)
    lines = []
    for page_id, vector in embeddings.items():
        truncated_id = page_id.encode("utf-8")[:64].decode("utf-8", errors="ignore")
        lines.append(json.dumps({"id": truncated_id, "values": vector}))
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
