"""Tolerant date parsing across sources.

Sources emit different formats: ISO 8601 (HN, GitHub, Exa) and RFC 822 (arXiv
RSS). We parse leniently and normalize to timezone-aware UTC; anything
unparseable returns None and is treated conservatively by callers (kept, not
dropped).
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for parser in (_iso, parsedate_to_datetime):
        try:
            dt = parser(value)
        except Exception:
            continue
        if dt is None:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return None
