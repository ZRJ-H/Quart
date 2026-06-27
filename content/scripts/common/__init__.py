#!/usr/bin/env python3
"""脚本公共模块：路径、文件读写、frontmatter、HTTP、日期与日志工具。

所有采集 / 构建脚本共享的工具函数集中在此处，避免逻辑重复。
各函数保持与原脚本一致的行为，仅作抽取复用，不改变外部输出。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

# 仓库根目录（scripts/common/__init__.py -> scripts -> 仓库根）。
VAULT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# wiki 页面的合法分类目录。
WIKI_TYPES: tuple[str, ...] = ("entities", "concepts", "sources", "synthesis")

FrontmatterValue = Union[str, int, float, Sequence[object]]


def setup_logging(level: int = logging.INFO) -> None:
    """配置脚本日志输出。

    使用 ``logging.basicConfig`` 做最简配置，输出纯消息文本（不带级别前缀），
    以贴近原脚本的 ``print`` 行为。重复调用是幂等的。

    Args:
        level: 日志级别，默认 ``logging.INFO``。
    """
    logging.basicConfig(level=level, format="%(message)s")


def date_format(dt: Optional[datetime] = None) -> str:
    """将日期格式化为统一的 ``YYYY-MM-DD`` 字符串。

    Args:
        dt: 待格式化的 ``datetime``；为 ``None`` 时使用当前时间。

    Returns:
        形如 ``2026-06-13`` 的日期字符串。
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")


def safe_slug(text: str) -> str:
    """从标题或 URL 生成安全的文件名 slug。

    去除协议头与非单词字符，空白与连字符归一为单个 ``-``，转小写并截断到 80 字符。

    Args:
        text: 原始标题或 URL。

    Returns:
        可安全用作文件名的 slug。
    """
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-").lower()[:80]


def wiki_path(type: str, name: str) -> Path:
    """生成 wiki 页面的绝对路径。

    Args:
        type: wiki 分类目录，应为 ``entities`` / ``concepts`` / ``sources`` /
            ``synthesis`` 之一。
        name: 页面名（不含 ``.md`` 扩展名）。

    Returns:
        指向 ``wiki/<type>/<name>.md`` 的 ``Path``。
    """
    return VAULT_ROOT / "wiki" / type / f"{name}.md"


def read_raw(path: Union[str, Path]) -> str:
    """安全读取文本文件，容错处理编码问题。

    以 UTF-8 读取并用 ``errors="replace"`` 替换无法解码的字节，避免脚本因
    个别坏字符崩溃。

    Args:
        path: 文件路径。

    Returns:
        文件文本内容。
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def serialize_frontmatter(frontmatter: Union[str, Mapping[str, FrontmatterValue]]) -> str:
    """将 frontmatter 序列化为 YAML 文本（不含外层 ``---`` 分隔符）。

    若传入字符串，则视为调用方已序列化好的内容，原样返回（去除首尾换行）。
    若传入映射：列表 / 元组渲染为 ``[a, b, c]``（裸值，逗号空格分隔），其余值
    直接转字符串。字符串值的引号由调用方自行决定（在值中自带），以保证与各脚本
    既有输出逐字节一致。

    Args:
        frontmatter: 已序列化的字符串，或键到值的映射。

    Returns:
        序列化后的 frontmatter 文本。
    """
    if isinstance(frontmatter, str):
        return frontmatter.strip("\n")
    lines = []
    for key, value in frontmatter.items():
        if isinstance(value, (list, tuple)):
            inner = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{inner}]")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def write_wiki_page(
    path: Union[str, Path],
    frontmatter: Union[str, Mapping[str, FrontmatterValue]],
    content: str,
) -> Path:
    """写入带 frontmatter 的 markdown 页面。

    自动创建父目录，组合为 ``---\\n<frontmatter>\\n---\\n\\n<content>`` 并以
    UTF-8 写入。``content`` 为 frontmatter 之后的正文（含正文首个标题）。

    Args:
        path: 输出文件路径。
        frontmatter: frontmatter 映射或已序列化的字符串。
        content: frontmatter 之后的正文内容。

    Returns:
        写入的文件 ``Path``。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fm_text = serialize_frontmatter(frontmatter)
    page = f"---\n{fm_text}\n---\n\n{content}"
    path.write_text(page, encoding="utf-8")
    return path


def extract_frontmatter(text: str) -> dict[str, str]:
    """解析 markdown 文本顶部的 YAML frontmatter。

    仅做简单的 ``key: value`` 解析，去除值两侧的引号；不解析列表 / 嵌套结构。

    Args:
        text: 完整的 markdown 文本。

    Returns:
        键值字符串映射；无 frontmatter 时返回空字典。
    """
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def http_get(
    url: str,
    headers: Optional[Mapping[str, str]] = None,
    timeout: int = 30,
) -> str:
    """发起 HTTP GET 请求并返回响应文本。

    使用 ``requests``（延迟导入，避免给无需联网的脚本引入依赖），带超时与
    ``raise_for_status`` 校验。

    Args:
        url: 目标 URL。
        headers: 可选请求头。
        timeout: 超时秒数，默认 30。

    Returns:
        响应体文本。

    Raises:
        requests.HTTPError: 当响应状态码表示失败时。
    """
    import requests

    resp = requests.get(url, headers=dict(headers) if headers else None, timeout=timeout)
    resp.raise_for_status()
    return resp.text
