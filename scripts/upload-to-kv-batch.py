#!/usr/bin/env python3
"""Upload wiki-data-full.json to Cloudflare KV namespace in batches.

Usage:
  python3 scripts/upload-to-kv-batch.py <wiki-data-full.json>

Requires CLOUDFLARE_API_TOKEN environment variable.
Uses wrangler CLI for KV operations.
"""

import json
import os
import subprocess
import sys
import tempfile


def upload_batch(entries, batch_num, total_batches, namespace_id):
    """Upload a batch of entries to KV."""
    print(f"Uploading batch {batch_num}/{total_batches} ({len(entries)} entries)...")
    
    # Write bulk payload to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(entries, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["npx", "wrangler", "kv", "bulk", "put", tmp_path, "--namespace-id", namespace_id],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            print(f"ERROR: wrangler kv bulk put failed for batch {batch_num}:\n{result.stderr}", file=sys.stderr)
            return False
        print(f"Batch {batch_num} uploaded successfully")
        return True
    finally:
        os.unlink(tmp_path)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <wiki-data-full.json>", file=sys.stderr)
        sys.exit(1)

    data_file = sys.argv[1]
    if not os.path.exists(data_file):
        print(f"ERROR: File not found: {data_file}", file=sys.stderr)
        sys.exit(1)

    namespace_id = "d61189e9b8314bd48a975bb878392614"
    batch_size = 100

    with open(data_file, encoding="utf-8") as f:
        entries = json.load(f)

    print(f"Total entries: {len(entries)}")
    print(f"Batch size: {batch_size}")
    
    # Prepare batches
    kv_entries = []
    for entry in entries:
        key = entry["id"]
        value = json.dumps(entry, ensure_ascii=False)
        kv_entries.append({
            "key": key,
            "value": value,
            "base64": False,
        })
    
    # Split into batches
    batches = [kv_entries[i:i + batch_size] for i in range(0, len(kv_entries), batch_size)]
    print(f"Number of batches: {len(batches)}")
    
    # Upload each batch
    success_count = 0
    for i, batch in enumerate(batches, 1):
        if upload_batch(batch, i, len(batches), namespace_id):
            success_count += 1
        else:
            print(f"Failed to upload batch {i}")
    
    print(f"\nUpload complete: {success_count}/{len(batches)} batches successful")
    print(f"Total entries uploaded: {success_count * batch_size}")


if __name__ == "__main__":
    main()
