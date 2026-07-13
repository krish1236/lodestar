"""Exa web adapter — neural search over credible AI/agent sources.

The one query-constructing source: it searches for recent developments scoped to
a domain allowlist (`config/domains.yaml`), covering vendor blogs that have no
RSS. Requires `EXA_API_KEY`; without it the adapter degrades to empty (no error),
so the rest of the pipeline runs and it activates the moment the key is added.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import httpx

from ..models import Finding
from .base import FetchResult, SourceError

SEARCH = "https://api.exa.ai/search"
_LOOKBACK_DAYS = 3


def parse(results: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for r in results:
        url = r.get("url", "")
        findings.append(
            Finding(
                source="exa",
                external_id=r.get("id") or url,
                url=url,
                title=(r.get("title") or "(untitled)").strip(),
                published_at=r.get("publishedDate", ""),
                author=r.get("author"),
                summary=(r.get("text") or None),
                credibility_signals={"domain": urlsplit(url).netloc.lower().removeprefix("www.")},
                raw={"score": r.get("score")},
            )
        )
    return findings


class ExaAdapter:
    name = "exa"

    def __init__(self, query: str, domains: list[str]):
        self.query = query
        self.domains = domains

    def fetch(self, cap: int) -> FetchResult:
        key = os.environ.get("EXA_API_KEY")
        if not key:
            return FetchResult(findings=[], errors=[])  # graceful no-key skip

        start = (datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)).strftime(
            "%Y-%m-%d"
        )
        try:
            resp = httpx.post(
                SEARCH,
                headers={"x-api-key": key, "Content-Type": "application/json"},
                json={
                    "query": self.query,
                    "numResults": cap,
                    "category": "news",
                    "includeDomains": self.domains,
                    "startPublishedDate": start,
                    "contents": {"text": {"maxCharacters": 500}},
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            return FetchResult(findings=parse(resp.json().get("results", [])))
        except Exception as exc:  # fault isolation
            return FetchResult(findings=[], errors=[SourceError(self.name, str(exc))])
