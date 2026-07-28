"""Seen-keys — the never-lossy exact-dedup index.

A newline-delimited file of normalized keys, appended to every run. This is the
*correctness* guarantee for "never repeat": a key, once written, is kept forever
(tiny — a few dozen bytes each). Keys are URL-based, so the same item arriving
from two sources (a paper on arXiv and the same link on HN) dedups to one.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ..config import REPO_ROOT
from ..models import Finding

SEEN_PATH = REPO_ROOT / "state" / "seen_keys.txt"


def normalize_url(url: str) -> str:
    """Scheme+host lowercased, query/fragment dropped, trailing slash stripped.
    Shared by the seen-index and the feedback/fold join so keys line up."""
    p = urlsplit(url)
    return urlunsplit(((p.scheme or "https").lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))


def normalize_key(finding: Finding) -> str:
    """URL-based key; falls back to source:external_id when there is no URL."""
    if finding.url:
        return normalize_url(finding.url)
    return f"{finding.source}:{finding.external_id}"


def load(path: Path | None = None) -> set[str]:
    path = path or SEEN_PATH
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def filter_new(findings: list[Finding], seen: set[str]) -> list[Finding]:
    """Drop findings already in `seen`, and collapse within-run duplicates
    (same key from two sources this run) to the first occurrence."""
    fresh: list[Finding] = []
    local = set(seen)
    for f in findings:
        key = normalize_key(f)
        if key in local:
            continue
        local.add(key)
        fresh.append(f)
    return fresh


def append(findings: list[Finding], path: Path | None = None) -> None:
    path = path or SEEN_PATH
    if not findings:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for f in findings:
            fh.write(normalize_key(f) + "\n")
