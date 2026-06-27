#!/usr/bin/env python3
"""上传同义词表到 Cloudflare KV。

Usage:
  CLOUDFLARE_API_TOKEN=xxx python3 scripts/upload-synonyms.py synonyms.json

Requires CLOUDFLARE_API_TOKEN environment variable.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile

from common import setup_logging

log = logging.getLogger(__name__)

KV_NAMESPACE_ID = "d61189e9b8314bd48a975bb878392614"


def main() -> None:
    """脚本入口：读取同义词 JSON 并通过 wrangler 上传到 KV。"""
    setup_logging()
    if len(sys.argv) < 2:
        log.error(f"Usage: {sys.argv[0]} <synonyms.json>")
        sys.exit(1)

    synonyms_file = sys.argv[1]
    if not os.path.exists(synonyms_file):
        log.error(f"ERROR: File not found: {synonyms_file}")
        sys.exit(1)

    with open(synonyms_file, encoding="utf-8") as f:
        synonyms = json.load(f)

    log.info(f"上传同义词表：{len(synonyms)} 组")

    # 构建 KV 批量上传格式
    kv_entries = [{
        "key": "synonyms",
        "value": json.dumps(synonyms, ensure_ascii=False),
        "base64": False,
    }]

    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(kv_entries, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["npx", "wrangler", "kv", "bulk", "put", tmp_path, "--namespace-id", KV_NAMESPACE_ID],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            log.error(f"ERROR: wrangler kv bulk put failed:\n{result.stderr}")
            sys.exit(1)
        log.info("同义词表上传成功")
        log.info(result.stdout.strip())
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
