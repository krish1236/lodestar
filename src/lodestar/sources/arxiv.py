"""arXiv adapter — daily category RSS, keeping only newly-announced papers.

Uses the per-category RSS feeds (updated daily). We filter to `announce_type ==
new` so replacements and cross-lists don't resurface. Politeness: one request
per 3 seconds, per arXiv's terms. Affiliation is usually absent from the feed,
so credibility here is weak/best-effort (handled later).
"""

from __future__ import annotations

import time

import feedparser
import httpx

from ..models import Finding
from .base import FetchResult, SourceError

RSS = "https://rss.arxiv.org/rss/{category}"
_THROTTLE_SECONDS = 3.0


def _announce_type(entry) -> str:
    for key, value in entry.items():
        if key.endswith("announce_type"):
            return str(value).lower()
    return "new"  # if the feed omits it, treat as new


def parse(feed_text: str, cap: int) -> list[Finding]:
    parsed = feedparser.parse(feed_text)
    findings: list[Finding] = []
    for entry in parsed.entries:
        if _announce_type(entry) != "new":
            continue
        link = entry.get("link", "")
        findings.append(
            Finding(
                source="arxiv",
                external_id=entry.get("id") or link,
                url=link,
                title=(entry.get("title") or "(untitled)").strip(),
                published_at=entry.get("published", ""),
                author=entry.get("author"),
                summary=(entry.get("summary") or None),
                raw={"category": entry.get("category")},
            )
        )
        if len(findings) >= cap:
            break
    return findings


class ArxivAdapter:
    name = "arxiv"

    def __init__(self, categories: list[str], cap: int = 15):
        self.categories = categories
        self._cap = cap

    def fetch(self, cap: int) -> FetchResult:
        cap = min(cap, self._cap)
        findings: list[Finding] = []
        errors: list[SourceError] = []
        for i, category in enumerate(self.categories):
            if i:
                time.sleep(_THROTTLE_SECONDS)  # <= 1 request / 3s
            try:
                resp = httpx.get(RSS.format(category=category), timeout=20.0)
                resp.raise_for_status()
                findings.extend(parse(resp.text, cap))
            except Exception as exc:  # fault isolation
                errors.append(SourceError(self.name, f"{category}: {exc}"))
        return FetchResult(findings=findings[:cap], errors=errors)
