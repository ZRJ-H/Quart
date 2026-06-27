#!/usr/bin/env python3
"""从 wiki 页面自动生成同义词候选表。

扫描 wiki/ 目录下所有页面，提取：
1. tags 字段中的标签
2. 标题变体（中英文、大小写）
3. 内容中的 [[wikilinks]] 引用

输出 synonyms-candidates.json 供人工审核。

Usage:
  python3 scripts/build-synonyms.py wiki/ -o synonyms-candidates.json
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Union

from common import read_raw, setup_logging

log = logging.getLogger(__name__)


def extract_frontmatter(content: str) -> dict[str, Union[str, list[str]]]:
    """提取 YAML frontmatter（支持简单列表解析）。

    Args:
        content: 完整 markdown 文本。

    Returns:
        键到字符串或字符串列表的映射。
    """
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, Union[str, list[str]]] = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if val.startswith('[') and val.endswith(']'):
                # 简单解析列表
                items = [v.strip().strip('"\'') for v in val[1:-1].split(',')]
                # 过滤空字符串
                fm[key] = [v for v in items if v]
            else:
                fm[key] = val
    return fm


def extract_wikilinks(content: str) -> list[str]:
    """提取 [[wikilinks]]。

    Args:
        content: 完整 markdown 文本。

    Returns:
        去重后的链接目标列表。
    """
    links = []
    regex = r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]'
    for match in re.finditer(regex, content):
        links.append(match.group(1).strip())
    return list(set(links))


chinese_to_english = {
    '人工智能': 'AI',
    '大语言模型': 'LLM',
    '大模型': 'LLM',
    '智能体': 'Agent',
    '自主代理': 'Agent',
    '检索增强生成': 'RAG',
    '向量数据库': 'vector database',
    '注意力机制': 'attention',
    '变换器': 'transformer',
    '深度学习': 'deep learning',
    '机器学习': 'machine learning',
    '神经网络': 'neural network',
    '反向传播': 'backpropagation',
    '梯度下降': 'gradient descent',
    '损失函数': 'loss function',
    '过拟合': 'overfitting',
    '正则化': 'regularization',
    '卷积神经网络': 'CNN',
    '循环神经网络': 'RNN',
    '生成对抗网络': 'GAN',
    '强化学习': 'reinforcement learning',
    '自然语言处理': 'NLP',
    '计算机视觉': 'computer vision',
    '预训练': 'pre-training',
    '微调': 'fine-tuning',
    '提示工程': 'prompt engineering',
    '上下文学习': 'in-context learning',
    '思维链': 'chain of thought',
    '多模态': 'multimodal',
    '嵌入': 'embedding',
    '分词': 'tokenization',
    '注意力': 'attention',
    '自注意力': 'self-attention',
    '多头注意力': 'multi-head attention',
    '位置编码': 'positional encoding',
    '残差连接': 'residual connection',
    '层归一化': 'layer normalization',
    'dropout': 'dropout',
    '批归一化': 'batch normalization',
}


def build_name_variants(name: str, existing_names: set[str]) -> set[str]:
    """生成名称变体，只添加实际存在于 wiki 中的变体。

    Args:
        name: 页面名。
        existing_names: 全部已知页面名集合。

    Returns:
        包含 ``name`` 自身及有效变体的集合。
    """
    variants = set()
    variants.add(name)

    lower_name = name.lower()
    if lower_name != name and lower_name in existing_names:
        variants.add(lower_name)

    upper_name = name.upper()
    if upper_name != name and upper_name in existing_names:
        variants.add(upper_name)

    # 中英文映射
    for cn, en in chinese_to_english.items():
        if name == cn and en in existing_names:
            variants.add(en)
        if name == en and cn in existing_names:
            variants.add(cn)

    return variants


def main() -> None:
    """脚本入口：扫描 wiki 目录并生成同义词候选 JSON。"""
    import argparse
    setup_logging()
    parser = argparse.ArgumentParser(description='从 wiki 生成同义词候选')
    parser.add_argument('wiki_dir', help='wiki 目录路径')
    parser.add_argument('-o', '--output', default='synonyms-candidates.json', help='输出文件')
    args = parser.parse_args()

    wiki_dir = Path(args.wiki_dir)
    if not wiki_dir.exists():
        log.error(f"ERROR: {wiki_dir} not found")
        sys.exit(1)

    # 收集所有页面信息
    pages = {}  # id -> {name, tags, links, category}
    tag_pages = defaultdict(set)  # tag -> [page_ids]

    for md_file in wiki_dir.rglob('*.md'):
        try:
            content = read_raw(md_file)
        except Exception:
            continue

        fm = extract_frontmatter(content)
        if not fm.get('name'):
            continue

        # 计算相对路径作为 id
        rel_path = md_file.relative_to(wiki_dir).with_suffix('')
        page_id = str(rel_path)

        name = fm['name']
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.strip('[]').split(',')]
        category = fm.get('category', '')
        links = extract_wikilinks(content)

        pages[page_id] = {
            'name': name,
            'tags': tags,
            'links': links,
            'category': category,
        }

        for tag in tags:
            tag_pages[tag].add(page_id)

    log.info(f"扫描完成：{len(pages)} 个页面")

    # 构建索引
    name_to_pid = {}  # name -> pid
    filename_to_pid = {}  # filename (stem) -> pid
    for pid, page in pages.items():
        name = page['name']
        if name in name_to_pid:
            log.warning(f"WARNING: 重复的页面名 '{name}'：{name_to_pid[name]} 和 {pid}")
        name_to_pid[name] = pid
        filename = Path(pid).stem
        filename_to_pid[filename] = pid

    existing_names = set(name_to_pid.keys())

    # 构建同义词候选
    candidates = defaultdict(set)

    # 1. 基于 tags 的同义词
    # 只处理有 3 个以上页面共享的 tag（表示这个 tag 是一个明确的主题）
    for tag, page_ids in tag_pages.items():
        if len(page_ids) >= 3:
            page_names = [pages[pid]['name'] for pid in page_ids]
            for name in page_names:
                for other_name in page_names:
                    if name != other_name:
                        candidates[name].add(other_name)

    # 2. 基于 wikilinks 的同义词
    # 如果 A 页面链接到 B，且 B 也链接到 A，它们可能相关
    for pid, page in pages.items():
        for link_name in page['links']:
            # 同时检查 name 和 filename
            other_pid = name_to_pid.get(link_name) or filename_to_pid.get(link_name)
            if other_pid:
                other_page = pages[other_pid]
                # 双向链接 → 可能相关
                if page['name'] in other_page['links']:
                    candidates[page['name']].add(link_name)
                    candidates[link_name].add(page['name'])

    # 3. 基于名称变体
    for page in pages.values():
        name = page['name']
        variants = build_name_variants(name, existing_names)
        for v in variants:
            if v != name:
                candidates[name].add(v)

    # 转换为最终格式
    result = {}
    for name, synonyms in candidates.items():
        if synonyms:
            result[name] = sorted(list(synonyms))

    # 写入文件
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    log.info(f"生成同义词候选：{len(result)} 组")
    log.info(f"输出到：{args.output}")
    log.info("请人工审核后上传到 KV")


if __name__ == '__main__':
    main()
