"""Hacker News adapter — the cleanest API, chosen as the Phase 0 first source.

Uses the Algolia HN Search API front-page tag. Credibility signals (points,
comments) are attached raw; author karma lookup and weighting come later.
"""

from __future__ import annotations

import httpx

from ..models import Finding
from .base import FetchResult, SourceError

ALGOLIA_SEARCH = "https://hn.algolia.com/api/v1/search"
HN_USER = "https://hacker-news.firebaseio.com/v0/user/{user}.json"
HN_ITEM = "https://news.ycombinator.com/item?id="


def _karma_map(authors: list[str]) -> dict[str, dict]:
    """One /user lookup per unique author — karma + account age (the cleanest
    credibility signal across all our sources)."""
    out: dict[str, dict] = {}
    for author in {a for a in authors if a}:
        try:
            resp = httpx.get(HN_USER.format(user=author), timeout=10.0)
            resp.raise_for_status()
            data = resp.json() or {}
            out[author] = {"karma": data.get("karma"), "account_created": data.get("created")}
        except Exception:
            continue  # missing karma is non-fatal
    return out


class HackerNewsAdapter:
    name = "hackernews"

    def fetch(self, cap: int) -> FetchResult:
        try:
            resp = httpx.get(
                ALGOLIA_SEARCH,
                params={"tags": "front_page", "hitsPerPage": cap},
                timeout=20.0,
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", [])
        except Exception as exc:  # fault isolation — degrade, don't abort
            return FetchResult(findings=[], errors=[SourceError(self.name, str(exc))])

        findings: list[Finding] = []
        for hit in hits:
            object_id = str(hit.get("objectID", ""))
            url = hit.get("url") or f"{HN_ITEM}{object_id}"
            findings.append(
                Finding(
                    source=self.name,
                    external_id=object_id,
                    url=url,
                    title=hit.get("title") or "(untitled)",
                    published_at=hit.get("created_at", ""),
                    author=hit.get("author"),
                    credibility_signals={
                        "points": hit.get("points"),
                        "num_comments": hit.get("num_comments"),
                    },
                    raw=hit,
                )
            )

        karma = _karma_map([f.author for f in findings])
        for f in findings:
            if f.author in karma:
                f.credibility_signals.update(karma[f.author])
        return FetchResult(findings=findings)
