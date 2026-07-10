"""The normalized shape every source produces and everything downstream speaks.

`Finding` is the spine of the system: sources map their payloads onto it,
dedup/verify/rank operate on it, and the digest renders from it. Keeping this
one type stable is what lets sources be swapped behind the adapter seam.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finding:
    source: str  # adapter name, e.g. "hackernews"
    external_id: str  # stable per-source id (HN objectID, arxiv id, release tag, ...)
    url: str
    title: str
    published_at: str  # ISO 8601 string
    summary: str | None = None
    author: str | None = None
    # Raw credibility signals attached at collection (no judgment here):
    # e.g. {"points": 210, "num_comments": 88} for HN.
    credibility_signals: dict = field(default_factory=dict)
    # One-line "why this matters for you", filled by the synthesizer (LLM).
    why: str | None = None
    # Source-specific payload, kept for provenance.
    raw: dict = field(default_factory=dict)
