#!/usr/bin/env python3
"""清理菜鸟教程的重复内容，只保留每个教程的唯一部分。

用法:
  python3 runoob-clean.py
"""

import os
import re

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "articles")


def extract_unique_content(filepath):
    """提取教程的唯一内容（去掉重复的子页面）"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 分割成行
    lines = content.split("\n")
    
    # 找到 frontmatter 结束位置
    frontmatter_end = 0
    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if in_frontmatter:
                frontmatter_end = i
                break
            else:
                in_frontmatter = True
    
    # 保留 frontmatter
    frontmatter = "\n".join(lines[:frontmatter_end + 1])
    
    # 找到目录结束位置（第一个 "---" 之后）
    content_start = frontmatter_end + 1
    
    # 找到实际内容开始位置（跳过标题和基本信息）
    actual_content_start = content_start
    for i in range(content_start, len(lines)):
        line = lines[i].strip()
        if line.startswith("## 概述") or line.startswith("## 简介") or line.startswith("## 介绍"):
            actual_content_start = i
            break
        # 如果遇到新的大标题，说明是实际内容开始
        if line.startswith("# ") and i > content_start + 5:
            actual_content_start = i
            break
    
    # 找到重复内容开始位置（通常是第二个 "---" 分隔符）
    duplicate_start = len(lines)
    separator_count = 0
    for i in range(actual_content_start, len(lines)):
        if lines[i].strip() == "---":
            separator_count += 1
            if separator_count >= 2:  # 第二个分隔符通常是重复内容开始
                duplicate_start = i
                break
    
    # 提取唯一内容
    unique_lines = lines[actual_content_start:duplicate_start]
    
    # 清理内容
    unique_content = "\n".join(unique_lines)
    
    # 移除目录部分（如果存在）
    unique_content = re.sub(r'## 目录\n.*?(?=\n## |\n# |\Z)', '', unique_content, flags=re.DOTALL)
    
    # 清理多余空行
    unique_content = re.sub(r'\n{3,}', '\n\n', unique_content)
    
    # 组合 frontmatter 和内容
    result = frontmatter + "\n\n" + unique_content.strip()
    
    return result


def process_tutorials():
    """处理所有教程文件"""
    print("=== 清理菜鸟教程重复内容 ===\n")
    
    # 获取所有菜鸟教程文件
    runoob_files = [f for f in os.listdir(RAW_DIR) if f.startswith("wwwrunoob") and f.endswith(".md")]
    
    for filename in sorted(runoob_files):
        filepath = os.path.join(RAW_DIR, filename)
        
        # 读取原始内容
        with open(filepath, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        # 提取唯一内容
        unique_content = extract_unique_content(filepath)
        
        # 计算减少的字符数
        original_size = len(original_content)
        unique_size = len(unique_content)
        reduction = original_size - unique_size
        reduction_percent = (reduction / original_size) * 100 if original_size > 0 else 0
        
        print(f"{filename}:")
        print(f"  原始大小: {original_size:,} 字符")
        print(f"  清理后: {unique_size:,} 字符")
        print(f"  减少: {reduction:,} 字符 ({reduction_percent:.1f}%)")
        
        # 保存清理后的内容
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(unique_content)
        
        print(f"  已保存\n")
    
    print("=== 清理完成 ===")


if __name__ == "__main__":
    process_tutorials()
