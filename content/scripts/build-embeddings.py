#!/usr/bin/env python3
"""为 wiki 页面生成 embeddings。

使用阿里云通义千问 tongyi-embedding-vision-flash-2026-03-06 模型。

Usage:
  DASHSCOPE_API_KEY=xxx python3 scripts/build-embeddings.py worker/wiki-data-full.json -o embeddings.json

Requires DASHSCOPE_API_TOKEN environment variable.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Optional

from common import setup_logging

log = logging.getLogger(__name__)


def call_embedding_api(
    texts: list[str],
    api_key: str,
    max_retries: int = 3,
) -> Optional[list[list[float]]]:
    """调用通义千问 embedding API。

    Args:
        texts: 文本列表（最多 25 条）。
        api_key: DashScope API key。
        max_retries: 最大重试次数。

    Returns:
        embeddings 列表；全部重试失败时返回 ``None``。
    """
    import dashscope

    dashscope.api_key = api_key

    input_data = [{'text': t} for t in texts]

    for attempt in range(max_retries):
        try:
            resp = dashscope.MultiModalEmbedding.call(
                model="tongyi-embedding-vision-flash-2026-03-06",
                input=input_data
            )

            if resp.status_code == 200:
                return [item['embedding'] for item in resp.output['embeddings']]
            else:
                log.error(f"API 错误 (attempt {attempt + 1}): {resp.code} - {resp.message}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        except Exception as e:
            log.error(f"异常 (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return None


def truncate_text(text: str, max_chars: int = 2000) -> str:
    """截断文本到指定长度。

    Args:
        text: 原始文本。
        max_chars: 最大字符数。

    Returns:
        截断后的文本。
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def main() -> None:
    """脚本入口：解析参数，批量生成并保存 embeddings。"""
    import argparse
    setup_logging()
    parser = argparse.ArgumentParser(description='为 wiki 页面生成 embeddings')
    parser.add_argument('data_file', help='wiki-data-full.json 文件路径')
    parser.add_argument('-o', '--output', default='embeddings.json', help='输出文件')
    parser.add_argument('--batch-size', type=int, default=20, help='每批处理的页面数（最多 25）')
    parser.add_argument('--limit', type=int, default=0, help='限制处理的页面数（0=全部）')
    parser.add_argument('--resume', action='store_true', help='从上次中断处继续')
    args = parser.parse_args()

    api_key = os.environ.get('DASHSCOPE_API_KEY')
    if not api_key:
        log.error("ERROR: 请设置 DASHSCOPE_API_KEY 环境变量")
        sys.exit(1)

    if not os.path.exists(args.data_file):
        log.error(f"ERROR: 文件不存在: {args.data_file}")
        sys.exit(1)

    # 加载 wiki 数据
    log.info(f"加载 {args.data_file}...")
    with open(args.data_file, encoding='utf-8') as f:
        pages = json.load(f)

    log.info(f"共 {len(pages)} 个页面")

    # 加载已有的 embeddings（用于断点续传）
    existing = {}
    if args.resume and os.path.exists(args.output):
        log.info(f"加载已有 embeddings: {args.output}")
        with open(args.output, encoding='utf-8') as f:
            existing = json.load(f)
        log.info(f"已有 {len(existing)} 个 embeddings")

    # 筛选需要处理的页面
    to_process = []
    for page in pages:
        page_id = page['id']
        if page_id in existing:
            continue
        to_process.append(page)

    if args.limit > 0:
        to_process = to_process[:args.limit]

    log.info(f"需要处理: {len(to_process)} 个页面")

    if not to_process:
        log.info("所有页面都已处理完毕")
        return

    # 批量处理
    embeddings = dict(existing)  # 保留已有的
    total_batches = (len(to_process) + args.batch_size - 1) // args.batch_size

    for batch_idx in range(0, len(to_process), args.batch_size):
        batch = to_process[batch_idx:batch_idx + args.batch_size]
        batch_num = batch_idx // args.batch_size + 1

        # 准备文本
        texts = []
        ids = []
        for page in batch:
            # 使用 name + summary + tags 作为 embedding 输入
            name = page.get('name', '')
            summary = page.get('summary', '') or page.get('content', '')[:500]
            tags = ' '.join(page.get('tags', []))
            category = page.get('category', '')

            # 组合文本，截断到 2000 字符
            text = f"{name}\n{category}\n{tags}\n{summary}"
            text = truncate_text(text, 2000)

            texts.append(text)
            ids.append(page['id'])

        # 调用 API
        log.info(f"批次 {batch_num}/{total_batches}: 处理 {len(texts)} 个页面...")
        result = call_embedding_api(texts, api_key)

        if result:
            for page_id, embedding in zip(ids, result):
                embeddings[page_id] = embedding
            log.info(f"  成功: {len(result)} 个 embeddings")
        else:
            log.error("  失败: 跳过这批")

        # 每 5 个批次保存一次
        if batch_num % 5 == 0:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(embeddings, f)
            log.info(f"  已保存中间结果 ({len(embeddings)} 个)")

        # 避免 API 限流
        time.sleep(0.5)

    # 保存最终结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f)

    log.info(f"\n完成！共生成 {len(embeddings)} 个 embeddings")
    log.info(f"输出到: {args.output}")


if __name__ == '__main__':
    main()
