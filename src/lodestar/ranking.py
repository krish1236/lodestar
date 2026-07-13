"""Ranking — a deterministic formula over per-item scores.

Gates (can kill an item): relevance. (novelty and signal are 1.0 in v1 —
semantic novelty is Phase 2.4, the substance signal is the verifier, Phase 2.1.)
Booster (can only lift, never kill): credibility, in [1, 2].

Highlights are chosen on the *universal* axis (relevance) so cross-source items
are comparable; within a section, items sort by the credibility-boosted score
(like-with-like). See Topic 7/9.
"""

from __future__ import annotations

import math

from .models import Finding

SECTION_OF = {
    "arxiv": "Papers",
    "github": "Releases",
    "hackernews": "Discussion",
    "exa": "Discussion",
}
SECTION_ORDER = ["Papers", "Releases", "Discussion", "Other"]

RELEVANCE_THRESHOLD = 0.3  # below this an item is off-mission and dropped


def _saturate(value, ref: float) -> float:
    if not value or value <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(ref))


def credibility_boost(signals: dict) -> float:
    """Map heterogeneous raw signals to a bounded [1, 2] multiplier. Log-
    saturation stops one viral outlier from dominating; unknown authors get 1.0
    (no penalty)."""
    boost = 1.0
    if signals.get("trusted"):
        boost += 0.5
    boost += 0.3 * _saturate(signals.get("karma"), 5000)
    boost += 0.3 * _saturate(signals.get("stars"), 20000)
    return min(boost, 2.0)


def rank(findings: list[Finding], threshold: float = RELEVANCE_THRESHOLD) -> list[Finding]:
    kept: list[Finding] = []
    for f in findings:
        r = f.relevance if f.relevance is not None else 0.5
        if r < threshold:
            continue  # off-mission — dropped from the digest
        f.rank_score = r * credibility_boost(f.credibility_signals)
        kept.append(f)
    return kept


def build_sections(
    ranked: list[Finding], n_highlights: int = 5
) -> tuple[list[Finding], dict[str, list[Finding]]]:
    highlights = sorted(ranked, key=lambda f: (f.relevance or 0), reverse=True)[:n_highlights]
    sections: dict[str, list[Finding]] = {}
    for f in sorted(ranked, key=lambda f: (f.rank_score or 0), reverse=True):
        sections.setdefault(SECTION_OF.get(f.source, "Other"), []).append(f)
    ordered = {s: sections[s] for s in SECTION_ORDER if s in sections}
    return highlights, ordered
