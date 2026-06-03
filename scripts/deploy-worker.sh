#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VAULT="${1:-$HOME/Documents/Obsidian}"

echo "=== Building wiki index from: $VAULT ==="
python3 "$SCRIPT_DIR/build-wiki-index.py" "$VAULT" \
  --light-output "$PROJECT_DIR/worker/wiki-index-light.json" \
  --full-output "$PROJECT_DIR/worker/wiki-data-full.json" \
  -o "$PROJECT_DIR/worker/wiki-data.json"

echo ""
echo "=== Uploading full data to KV ==="
cd "$PROJECT_DIR/worker"
python3 "$SCRIPT_DIR/upload-to-kv.py" "$PROJECT_DIR/worker/wiki-data-full.json"

echo ""
echo "=== Deploying Worker ==="
wrangler deploy

echo ""
echo "✓ Done. Worker live at: https://doge-wiki-search.zstufjj2004.workers.dev"
