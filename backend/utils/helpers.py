"""通用工具函数"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, UTC
from typing import Any


def generate_id(prefix: str = "", length: int = 8) -> str:
    """生成唯一 ID"""
    import uuid
    uid = uuid.uuid4().hex[:length]
    return f"{prefix}{uid}" if prefix else uid


def safe_str(value: Any) -> str:
    """安全转换为字符串"""
    if value is None:
        return ""
    return str(value).strip()


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def extract_urls(text: str) -> list[str]:
    """从文本中提取 URL"""
    url_pattern = re.compile(
        r"https?://[^\s<>\"']+",
        re.IGNORECASE,
    )
    return url_pattern.findall(text)


def hash_text(text: str) -> str:
    """计算文本的 SHA256 哈希"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_iso_datetime(value: str | None) -> datetime | None:
    """解析 ISO 格式的时间字符串"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """将列表分成固定大小的块"""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """扁平化嵌套字典"""
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
