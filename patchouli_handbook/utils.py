from __future__ import annotations

import re


def safe_slug(value: str, *, max_length: int = 64) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        normalized = "job"
    return normalized[:max_length]
