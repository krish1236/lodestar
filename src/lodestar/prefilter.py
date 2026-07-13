"""Cheap, deterministic candidate pre-filter — runs before the LLM stages.

Two jobs, no LLM:
  1. Keyword relevance — high-volume/low-curation sources (arXiv, HN) must have
     a title/summary matching the interest keywords; curated sources pass
     through (they're already scoped by watchlist/domain config).
  2. Per-source caps — bound how many candidates from each source reach the
     expensive per-item relevance/verify work.

This is what keeps arXiv's daily flood from blowing up cost and latency.
"""

from __future__ import annotations

from .models import Finding


def prefilter(findings: list[Finding], cfg: dict) -> list[Finding]:
    keywords = [k.lower() for k in cfg.get("keywords", [])]
    filtered_sources = set(cfg.get("filtered_sources", []))
    caps: dict = cfg.get("caps", {})

    # 1. keyword relevance (only for filtered sources)
    relevant: list[Finding] = []
    for f in findings:
        if f.source in filtered_sources:
            text = f"{f.title} {f.summary or ''}".lower()
            if keywords and not any(k in text for k in keywords):
                continue
        relevant.append(f)

    # 2. per-source cap (preserve order; order carries recency)
    counts: dict[str, int] = {}
    capped: list[Finding] = []
    for f in relevant:
        cap = caps.get(f.source)
        seen = counts.get(f.source, 0)
        if cap is not None and seen >= cap:
            continue
        counts[f.source] = seen + 1
        capped.append(f)
    return capped
