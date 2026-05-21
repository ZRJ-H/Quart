#!/bin/bash
set -e
echo "[postinstall] Filtering old content..."
python3 scripts/filter-old-content.py vault-content

echo "[postinstall] Building wiki index..."
python3 scripts/build-wiki-index.py vault-content -o worker/wiki-data.json
