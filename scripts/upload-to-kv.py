#!/usr/bin/env python3
"""Incrementally upload wiki-data-full.json to Cloudflare KV.

只上传内容有变化的条目：每条 KV 的 metadata 里存内容哈希，上传前用
`wrangler kv key list` 取回远端各键的哈希，仅 put 哈希变化/新增的条目。
这样每天写入数 = 变化条目数，稳低于免费版每日 1000 次写入额度。

Usage:
  python3 upload-to-kv.py <wiki-data-full.json>

Requires CLOUDFLARE_API_TOKEN environment variable. Uses wrangler CLI.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile

NAMESPACE_ID = "d61189e9b8314bd48a975bb878392614"
MAX_WRITES_PER_RUN = 900  # 保守低于免费版每日 1000 次写入额度；超出部分下次部署继续（首次全量会分几天收敛）


def content_hash(value):
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def list_remote_hashes():
    """返回 {key: hash}（来自 KV metadata）。失败时返回 {} → 退化为全量上传。"""
    try:
        result = subprocess.run(
            ["npx", "wrangler", "kv", "key", "list",
             "--namespace-id", NAMESPACE_ID, "--remote"],
            capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0:
            print(f"WARNING: kv key list 失败，退化为全量比对:\n{result.stderr}", file=sys.stderr)
            return {}
        keys = json.loads(result.stdout)
        out = {}
        for k in keys:
            md = k.get("metadata") or {}
            out[k.get("name")] = md.get("h")
        return out
    except Exception as e:
        print(f"WARNING: kv key list 异常，退化为全量比对: {e}", file=sys.stderr)
        return {}


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

    remote = list_remote_hashes()

    # 只挑哈希变化/新增的条目，并把新哈希写入 metadata
    kv_entries = []
    for entry in entries:
        key = entry["id"]
        value = json.dumps(entry, ensure_ascii=False)
        h = content_hash(value)
        if remote.get(key) == h:
            continue  # 内容未变，跳过
        kv_entries.append({
            "key": key,
            "value": value,
            "metadata": {"h": h},
            "base64": False,
        })

    unchanged = len(entries) - len(kv_entries)
    print(f"共 {len(entries)} 条；需上传 {len(kv_entries)} 条（变化/新增），跳过 {unchanged} 条未变")

    if len(kv_entries) > MAX_WRITES_PER_RUN:
        print(f"变化 {len(kv_entries)} 条超过单次上限 {MAX_WRITES_PER_RUN}（免费版每日额度），"
              f"本次只传前 {MAX_WRITES_PER_RUN} 条，其余下次部署继续")
        kv_entries = kv_entries[:MAX_WRITES_PER_RUN]

    # 写出本次处理的变化 id 列表（供增量嵌入步骤复用，只嵌变化条目）；空也写便于下游判断
    changed_out = os.environ.get("CHANGED_IDS_OUT")
    if changed_out:
        with open(changed_out, "w", encoding="utf-8") as cf:
            json.dump([e["key"] for e in kv_entries], cf, ensure_ascii=False)
        print(f"已写出 {len(kv_entries)} 个变化 id → {changed_out}（供增量嵌入）")

    if not kv_entries:
        print("KV 已是最新，无需上传。")
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(kv_entries, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["npx", "wrangler", "kv", "bulk", "put", tmp_path,
             "--namespace-id", NAMESPACE_ID, "--remote"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            # KV 免费版每日写入额度（code 10048）属可恢复错误：
            # 降级为警告，不阻断后续的 worker 部署（KV 数据将在额度重置后的下次部署更新）
            if "usage limit" in result.stderr or "10048" in result.stderr:
                print(f"WARNING: KV 写入触达每日额度，跳过本次 KV 更新（worker 仍会部署）:\n{result.stderr}", file=sys.stderr)
                return
            print(f"ERROR: wrangler kv bulk put failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
        print(f"成功上传 {len(kv_entries)} 条变化条目到 KV")
        print(result.stdout.strip())
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
