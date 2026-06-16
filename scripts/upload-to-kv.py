#!/usr/bin/env python3
"""Upload wiki-data-full.json to Cloudflare KV namespace.

Usage:
  python3 upload-to-kv.py <wiki-data-full.json>

Requires CLOUDFLARE_API_TOKEN environment variable.
Uses wrangler CLI for KV operations.
"""

import json
import os
import subprocess
import sys
import tempfile


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <wiki-data-full.json>", file=sys.stderr)
        sys.exit(1)

    data_file = sys.argv[1]
    if not os.path.exists(data_file):
        print(f"ERROR: File not found: {data_file}", file=sys.stderr)
        sys.exit(1)

    with open(data_file, encoding="utf-8") as f:
        entries = json.load(f)

    print(f"Uploading {len(entries)} entries to KV...")

    # Use wrangler kv bulk put for efficiency
    # wrangler expects a JSON array of {key, value, base64} objects
    kv_entries = []
    for entry in entries:
        key = entry["id"]
        value = json.dumps(entry, ensure_ascii=False)
        kv_entries.append({
            "key": key,
            "value": value,
            "base64": False,
        })

    # Write bulk payload to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(kv_entries, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["npx", "wrangler", "kv", "bulk", "put", tmp_path, "--namespace-id", "d61189e9b8314bd48a975bb878392614", "--remote"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            print(f"ERROR: wrangler kv bulk put failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
        print(f"Successfully uploaded {len(entries)} entries to KV")
        print(result.stdout.strip())
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
