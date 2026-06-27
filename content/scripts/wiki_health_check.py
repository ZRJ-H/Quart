#!/usr/bin/env python3
"""Wiki 健康检查：扫描 frontmatter、断链、孤儿页。

扫描 wiki/ 下 entities/concepts/sources 目录，检查：
1. Frontmatter 完整性（必填字段、日期格式、tags 格式）
2. 孤儿页（entities/concepts 中无入站 [[wikilink]] 的页面）
3. 断链（引用不存在的页面）

输出 JSON 报告到 stdout。

用法:
  python3 scripts/wiki_health_check.py                     # 输出到 stdout
  python3 scripts/wiki_health_check.py -o report.json      # 保存到文件
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

WIKI = Path(__file__).resolve().parent.parent / "wiki"
VAULT = WIKI.parent
SCAN_DIRS = ["entities", "concepts", "sources"]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")

# 各类型必填字段
REQUIRED: dict[str, list[str]] = {
    "entity": ["type", "name", "last_updated"],
    "concept": ["type", "name", "last_updated"],
    "source": ["type", "title", "date_accessed"],
}
DATE_FIELDS = ["first_seen", "last_updated", "date_accessed", "date_published", "date"]

# 根据目录推断类型
INFER_TYPE = {"entities": "entity", "concepts": "concept", "sources": "source"}


def parse_frontmatter(text: str) -> Optional[dict[str, tuple[str, str]]]:
    """解析 YAML frontmatter，返回 {key: (value_str, raw_line)}。

    Args:
        text: 完整 markdown 文本。

    Returns:
        frontmatter 映射；无 frontmatter 时返回 None。
    """
    if not text.startswith("---"):
        return None
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm: dict[str, tuple[str, str]] = {}
    for ln in lines[1:end]:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", ln)
        if m:
            fm[m.group(1)] = (m.group(2).strip(), ln)
    return fm


def basename_no_ext(path: Path) -> str:
    return path.stem


def norm_link(target: str) -> str:
    """规范化 wikilink 目标：去除别名/锚点/路径，只取 basename。"""
    t = target.split("|")[0].split("#")[0].replace("\\", "/").strip()
    if "/" in t:
        t = t.split("/")[-1]
    return t.strip()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Wiki 健康检查")
    parser.add_argument("-o", "--output", help="输出到文件（默认 stdout）")
    args = parser.parse_args()

    # ---- 构建全库页面名称集合 ----
    all_md = list(VAULT.rglob("*.md"))
    vault_names = {basename_no_ext(p) for p in all_md}

    # ---- 收集 wiki 页面（扫描目录 + synthesis，后者贡献入链） ----
    wiki_pages: dict[str, Path] = {}
    for d in SCAN_DIRS + ["synthesis"]:
        for p in (WIKI / d).rglob("*.md"):
            wiki_pages[str(p.relative_to(WIKI))] = p

    name_to_rel: dict[str, str] = {}
    for rel, ap in wiki_pages.items():
        name_to_rel.setdefault(basename_no_ext(ap), rel)

    # ---- 逐页扫描 ----
    frontmatter_issues: list[dict[str, Any]] = []
    broken_links: list[dict[str, str]] = []
    inbound: dict[str, int] = {}
    pages_without_fm = 0
    pages_missing_fields = 0
    total_pages = 0

    for rel, ap in sorted(wiki_pages.items()):
        top = rel.split(os.sep)[0]
        text = ap.read_text(encoding="utf-8", errors="replace")
        is_scan = top in SCAN_DIRS

        if is_scan:
            total_pages += 1
            fm = parse_frontmatter(text)
            issues: list[str] = []

            if fm is None:
                issues.append("缺少 frontmatter")
                pages_without_fm += 1
            else:
                ftype = fm.get("type", (None,))[0]
                inferred = INFER_TYPE[top]
                req = REQUIRED.get(ftype, REQUIRED[inferred])

                if "type" not in fm:
                    issues.append("缺少必填字段 type")
                elif ftype not in REQUIRED:
                    issues.append(f"type 值异常: {ftype}")

                missing = False
                for field in req:
                    if field == "type":
                        continue
                    if field not in fm:
                        if field == "date_accessed" and "date_published" in fm:
                            continue
                        issues.append(f"缺少必填字段 {field}")
                        missing = True

                if "tags" in fm:
                    tval = fm["tags"][0]
                    if (
                        tval
                        and tval not in ("null", "~")
                        and not (tval.startswith("[") and tval.endswith("]"))
                    ):
                        issues.append("tags 字段不是列表格式")

                for df in DATE_FIELDS:
                    if df in fm:
                        dv = fm[df][0]
                        if dv and not DATE_RE.match(dv):
                            issues.append(f"{df} 日期格式非 YYYY-MM-DD: {dv}")

                if missing:
                    pages_missing_fields += 1

            if issues:
                frontmatter_issues.append({"file": rel, "issues": issues})

        # ---- 提取正文中的 wikilinks ----
        body = text
        if text.startswith("---"):
            parts = text.split("\n")
            for i in range(1, len(parts)):
                if parts[i].strip() == "---":
                    body = "\n".join(parts[i + 1 :])
                    break

        for m in WIKILINK_RE.finditer(body):
            tgt = norm_link(m.group(1))
            if not tgt:
                continue
            inbound[tgt] = inbound.get(tgt, 0) + 1
            if tgt not in vault_names:
                broken_links.append({"source": rel, "broken_target": tgt})

    # ---- 孤儿页检测 ----
    orphans: list[str] = []
    for rel, ap in sorted(wiki_pages.items()):
        top = rel.split(os.sep)[0]
        if top not in ("entities", "concepts"):
            continue
        if inbound.get(basename_no_ext(ap), 0) == 0:
            orphans.append(rel)

    # ---- Top 引用 ----
    ref_list: list[tuple[str, int]] = []
    for name, cnt in inbound.items():
        if name in name_to_rel:
            rel = name_to_rel[name]
            if rel.split(os.sep)[0] in SCAN_DIRS:
                ref_list.append((rel, cnt))
    ref_list.sort(key=lambda x: (-x[1], x[0]))
    top_referenced = [{"page": r, "incoming_links": c} for r, c in ref_list[:25]]

    report = {
        "summary": {
            "total_pages": total_pages,
            "pages_without_frontmatter": pages_without_fm,
            "pages_with_missing_fields": pages_missing_fields,
            "orphan_pages_count": len(orphans),
            "broken_links_count": len(broken_links),
        },
        "frontmatter_issues": frontmatter_issues,
        "orphan_pages": orphans,
        "broken_links": broken_links,
        "top_referenced": top_referenced,
    }

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved to {args.output}")
        print(f"Summary: {report['summary']}")
    else:
        print(output)


if __name__ == "__main__":
    main()
