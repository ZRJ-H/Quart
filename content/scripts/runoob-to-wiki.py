#!/usr/bin/env python3
"""为菜鸟教程创建 Wiki 来源摘要页。

用法:
  python3 runoob-to-wiki.py
"""

import os
import re
from datetime import datetime

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "articles")
WIKI_SOURCES_DIR = os.path.join(VAULT, "wiki", "sources")
TODAY = datetime.now().strftime("%Y-%m-%d")


def extract_tutorial_info(filepath):
    """提取教程基本信息"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取 frontmatter
    lines = content.split("\n")
    title = ""
    url = ""
    in_frontmatter = False
    frontmatter_end = 0
    
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if in_frontmatter:
                frontmatter_end = i
                break
            else:
                in_frontmatter = True
                continue
        
        if in_frontmatter:
            if line.startswith("title:"):
                title = line.replace("title:", "").strip().strip('"')
            if line.startswith("url:"):
                url = line.replace("url:", "").strip()
    
    # 提取目录（前10个章节）
    toc = []
    in_toc = False
    for line in lines[frontmatter_end + 1:]:
        if line.strip() == "## 目录":
            in_toc = True
            continue
        if in_toc and line.startswith("- "):
            toc.append(line[2:].strip())
        if in_toc and (line.startswith("## ") or line.startswith("# ")):
            break
    
    # 提取概述（第一个 ## 概述 后的内容）
    overview = ""
    in_overview = False
    skip_title = False
    for line in lines[frontmatter_end + 1:]:
        if line.strip() == "## 概述":
            in_overview = True
            continue
        if in_overview:
            # 跳过标题（# 开头的行）
            if line.startswith("# "):
                skip_title = True
                continue
            # 遇到新的 ## 标题，停止
            if line.startswith("## "):
                break
            # 收集概述内容
            if line.strip():
                overview += line.strip() + "\n"
    
    return {
        "title": title,
        "url": url,
        "toc": toc[:10],  # 只取前10个
        "overview": overview.strip()[:500]  # 只取前500字符
    }


def create_source_page(tutorial_info, filename):
    """创建 Wiki 来源摘要页"""
    title = tutorial_info["title"]
    url = tutorial_info["url"]
    toc = tutorial_info["toc"]
    overview = tutorial_info["overview"]
    
    # 生成文件名
    source_filename = f"runoob-{filename.replace('wwwrunoobcom', '').replace('html.md', '')}.md"
    source_path = os.path.join(WIKI_SOURCES_DIR, source_filename)
    
    # 生成目录列表
    toc_text = "\n".join(f"- {item}" for item in toc) if toc else "无"
    
    # 生成内容
    content = f"""---
type: source
title: "{title}"
source_type: tutorial
url: {url}
date_accessed: {TODAY}
date_published: ?
tags: [tutorial, runoob, ai-agent]
---

# {title}

## 基本信息
- **来源**: 菜鸟教程
- **URL**: {url}
- **采集日期**: {TODAY}
- **类型**: 技术教程

## 概述
{overview if overview else "暂无概述"}

## 目录
{toc_text}

## 相关实体
- [[AI Agent]] - 主要教程内容
- [[Claude Code]] - 相关工具
- [[OpenCode]] - 相关工具
- [[Skills]] - 相关概念

## 相关概念
- [[AI Agent 生态]] - 教程主题
- [[多智能体编排]] - CrewAI/LangGraph 内容
- [[RAG]] - RAG 教程内容
- [[向量数据库]] - 向量数据库教程内容

## 个人思考
菜鸟教程提供了系统化的 AI Agent 学习路径，从基础概念到实际应用，适合作为入门参考资料。

## 最后更新
- 日期: {TODAY}
- 更新内容: 首次收录
"""
    
    with open(source_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return source_path


def main():
    print("=== 创建菜鸟教程 Wiki 来源摘要页 ===\n")
    
    # 确保目录存在
    os.makedirs(WIKI_SOURCES_DIR, exist_ok=True)
    
    # 获取所有菜鸟教程文件
    runoob_files = [f for f in os.listdir(RAW_DIR) if f.startswith("wwwrunoob") and f.endswith(".md")]
    
    created_files = []
    
    for filename in sorted(runoob_files):
        filepath = os.path.join(RAW_DIR, filename)
        
        # 提取教程信息
        tutorial_info = extract_tutorial_info(filepath)
        
        # 创建来源页
        source_path = create_source_page(tutorial_info, filename)
        
        print(f"创建: {os.path.basename(source_path)}")
        print(f"  标题: {tutorial_info['title']}")
        print(f"  章节数: {len(tutorial_info['toc'])}")
        print()
        
        created_files.append(source_path)
    
    print(f"=== 完成 ===")
    print(f"创建了 {len(created_files)} 个来源摘要页")
    print(f"保存位置: {WIKI_SOURCES_DIR}")


if __name__ == "__main__":
    main()
