#!/usr/bin/env python3
"""从菜鸟教程采集完整教程内容，合并所有子页面。

用法:
  python3 runoob-save.py <教程主页URL>
  python3 runoob-save.py https://www.runoob.com/ai-agent/ai-agent-tutorial.html

依赖: requests, beautifulsoup4
"""

import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "articles")
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def slugify(text):
    text = re.sub(r'https?://', '', text)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-').lower()[:80]


def fetch_page(url):
    """获取页面内容"""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_article_content(soup):
    """提取文章正文内容（只取 article-body 区域）"""
    # 优先查找 article-body
    article_body = soup.find("div", class_="article-body")
    if not article_body:
        article_body = soup.find("div", class_="article-intro")
    if not article_body:
        article_body = soup.find("article")
    if not article_body:
        # 降级到主内容区
        article_body = soup.find("div", class_="main")

    if not article_body:
        return ""

    # 移除不需要的元素
    for tag in article_body.find_all(["script", "style", "nav", "footer", "aside", 
                                       "noscript", "iframe", "svg", "button", "input",
                                       "div.article-heading-ad", "div.adsbygoogle",
                                       "div.coupon-container", "div.markdown-helper"]):
        tag.decompose()

    # 提取内容
    parts = []
    for el in article_body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", 
                                      "pre", "code", "blockquote", "hr", "br", "table",
                                      "div.code-block", "div.highlight"]):
        tag = el.name.lower()
        text = el.get_text(separator="\n", strip=True)
        
        if not text or len(text) < 2:
            continue
            
        # 跳过导航相关内容
        if any(skip in text for skip in ["分类导航", "站点信息", "意见反馈", "免责声明", 
                                          "关于我们", "文章归档", "关注微信", "Copyright",
                                          "我的收藏", "标记文章", "浏览历史", "点我分享笔记"]):
            continue

        if tag.startswith("h"):
            level = int(tag[1])
            parts.append(f"\n{'#' * level} {text}\n")
        elif tag == "p":
            parts.append(f"{text}\n")
        elif tag == "li":
            parts.append(f"- {text}")
        elif tag == "pre":
            parts.append(f"```\n{text}\n```\n")
        elif tag == "code":
            # 只处理独立的 code 块（不在 pre 内）
            if el.parent.name != "pre":
                parts.append(f"`{text}`")
        elif tag == "blockquote":
            parts.append(f"> {text}\n")
        elif tag == "hr":
            parts.append("---\n")
        elif tag == "br":
            parts.append("")
        elif tag == "table":
            # 简单处理表格
            rows = []
            for tr in el.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                parts.append("\n" + "\n".join(rows) + "\n")

    result = "\n".join(parts)
    # 清理多余空行
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def get_subpage_links(soup, base_url):
    """获取教程的所有子页面链接"""
    links = []
    seen = set()
    
    # 从 base_url 提取教程前缀
    path = urlparse(base_url).path
    prefix = "/".join(path.split("/")[:2]) + "/"  # 例如 /ai-agent/
    
    # 在整个页面中查找链接
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # 过滤出同一教程的子页面
        if href.startswith(prefix) and href.endswith(".html"):
            full_url = urljoin(base_url, href)
            if full_url not in seen and full_url != base_url:
                seen.add(full_url)
                links.append(full_url)
    
    return links


def extract_title(soup):
    """提取页面标题"""
    # 优先从 og:title 提取
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    
    # 从 title 标签提取
    if soup.title:
        title = soup.title.string.strip()
        # 移除 " | 菜鸟教程" 后缀
        title = re.sub(r'\s*\|\s*菜鸟教程$', '', title)
        return title
    
    # 从 h1 提取
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    
    return "未知标题"


def build_article(main_url, title, sections):
    """构建完整的教程文章"""
    content_parts = []
    for section in sections:
        if section["content"]:
            content_parts.append(f"## {section['title']}\n\n{section['content']}")
    
    full_content = "\n\n---\n\n".join(content_parts)
    
    article = f"""---
type: source
title: "{title}"
source_type: tutorial
url: {main_url}
date_accessed: {TODAY}
date_published: ?
tags: [tutorial, runoob, ai-agent]
---

# {title}

## 基本信息
- **来源**: 菜鸟教程
- **URL**: {main_url}
- **采集日期**: {TODAY}
- **章节数**: {len(sections)}

## 目录
{chr(10).join(f"- {s['title']}" for s in sections if s['content'])}

---

{full_content}
"""
    return article


def process_tutorial(main_url, max_pages=20):
    """处理一个完整的教程"""
    print(f"=== 开始采集教程 ===")
    print(f"主页: {main_url}")
    
    # 1. 获取主页
    print(f"\n[1/N] 获取主页...")
    html = fetch_page(main_url)
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)
    print(f"  标题: {title}")
    
    # 2. 获取子页面链接
    sub_links = get_subpage_links(soup, main_url)
    print(f"  发现 {len(sub_links)} 个子页面")
    
    # 3. 限制页面数
    sub_links = sub_links[:max_pages]
    
    # 4. 采集主页内容
    sections = []
    main_content = extract_article_content(soup)
    sections.append({"title": "概述", "url": main_url, "content": main_content})
    print(f"  主页内容: {len(main_content)} 字符")
    
    # 5. 采集子页面
    for i, link in enumerate(sub_links, 2):
        print(f"\n[{i}/{len(sub_links)+1}] 获取: {link}")
        try:
            time.sleep(0.5)  # 礼貌性延迟
            sub_html = fetch_page(link)
            sub_soup = BeautifulSoup(sub_html, "html.parser")
            sub_title = extract_title(sub_soup)
            sub_content = extract_article_content(sub_soup)
            sections.append({"title": sub_title, "url": link, "content": sub_content})
            print(f"  标题: {sub_title}")
            print(f"  内容: {len(sub_content)} 字符")
        except Exception as e:
            print(f"  错误: {e}")
    
    # 6. 构建完整文章
    article = build_article(main_url, title, sections)
    
    # 7. 保存
    slug = slugify(main_url)
    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, f"{slug}.md")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(article)
    
    total_chars = sum(len(s["content"]) for s in sections)
    print(f"\n=== 采集完成 ===")
    print(f"标题: {title}")
    print(f"章节数: {len(sections)}")
    print(f"总字符数: {total_chars}")
    print(f"保存位置: {out_path}")
    
    return out_path


def main():
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <教程主页URL>")
        print(f"示例: {sys.argv[0]} https://www.runoob.com/ai-agent/ai-agent-tutorial.html")
        sys.exit(1)
    
    url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    process_tutorial(url, max_pages)


if __name__ == "__main__":
    main()
