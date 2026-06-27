#!/usr/bin/env python3
"""运行 wiki_health_check.py 并把 JSON 输出格式化为 Markdown 报告。"""
import subprocess, json, datetime, sys
from pathlib import Path

VAULT = Path("/home/taskflow/Obsidian")
CHECKER = VAULT / "scripts/wiki_health_check.py"
OUT = VAULT / "wiki/health_report.md"

result = subprocess.run(
    ["python3", str(CHECKER)],
    capture_output=True, text=True, cwd=str(VAULT)
)
if result.returncode != 0:
    print(f"ERROR: health check failed\n{result.stderr}", file=sys.stderr)
    sys.exit(1)

data = json.loads(result.stdout)
s = data["summary"]
today = datetime.date.today().isoformat()

def section(title, items, fmt, limit=30):
    if not items:
        return [f"## {title}\n\n暂无问题\n"]
    lines = [f"## {title} ({len(items)} 个)\n"]
    for item in items[:limit]:
        lines.append(fmt(item))
    if len(items) > limit:
        lines.append(f"…… 还有 {len(items)-limit} 个")
    lines.append("")
    return lines

lines = [
    f"---",
    f"date: {today}",
    f"type: health_report",
    f"---",
    f"",
    f"# Wiki 健康报告 {today}",
    f"",
    f"| 指标 | 数值 |",
    f"|------|------|",
    f"| 总页面数 | {s['total_pages']} |",
    f"| 缺 frontmatter | {s['pages_without_frontmatter']} |",
    f"| 缺必填字段 | {s['pages_with_missing_fields']} |",
    f"| 孤儿页 | {s['orphan_pages_count']} |",
    f"| 断链 | {s['broken_links_count']} |",
    f"",
]

lines += section(
    "Frontmatter 问题", data["frontmatter_issues"],
    lambda x: f"- **{x['file']}**：{', '.join(x['issues'])}"
)
lines += section(
    "孤儿页", data["orphan_pages"],
    lambda x: f"- {x}"
)
lines += section(
    "断链", data["broken_links"],
    lambda x: f"- `{x['source']}` → `{x['broken_target']}`"
)

if data["top_referenced"]:
    lines += ["## 最高引用页 Top 10\n"]
    for r in data["top_referenced"][:10]:
        lines.append(f"- {r['page']}（{r['incoming_links']} 引用）")
    lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"报告已写入：{OUT}")
print(f"总页面={s['total_pages']}，孤儿={s['orphan_pages_count']}，断链={s['broken_links_count']}，frontmatter问题={s['pages_without_frontmatter']+s['pages_with_missing_fields']}")
