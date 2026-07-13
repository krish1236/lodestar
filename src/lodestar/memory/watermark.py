"""Watermarks — the per-source incremental cursor.

Records the newest published date seen per source. On the next run we skip
anything at or before it (an *efficiency* bound — seen-keys remains the
correctness guarantee, so a conservative/overlapping watermark is safe). The
cursor advances only from what was actually fetched, at run end.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import REPO_ROOT
from ..models import Finding
from .dates import parse_dt

WM_PATH = REPO_ROOT / "state" / "watermarks.json"


def load(path: Path | None = None) -> dict[str, str]:
    path = path or WM_PATH
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8") or "{}")


def save(watermarks: dict[str, str], path: Path | None = None) -> None:
    path = path or WM_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(watermarks, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def filter_newer(findings: list[Finding], watermarks: dict[str, str]) -> list[Finding]:
    out: list[Finding] = []
    for f in findings:
        mark = watermarks.get(f.source)
        d = parse_dt(f.published_at)
        md = parse_dt(mark) if mark else None
        if md and d and d <= md:
            continue  # older than the cursor -> already covered
        out.append(f)  # newer, or undated (kept conservatively)
    return out


def advance(findings: list[Finding], watermarks: dict[str, str]) -> dict[str, str]:
    updated = dict(watermarks)
    for f in findings:
        d = parse_dt(f.published_at)
        if not d:
            continue
        cur = parse_dt(updated.get(f.source)) if updated.get(f.source) else None
        if cur is None or d > cur:
            updated[f.source] = d.isoformat()
    return updated
