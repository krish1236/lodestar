"""Deterministic topic tagging.

An item's topics are the interest keywords (from prefilter config) that appear
in its title/summary. Used to tag item_shown events (so feedback can be folded
per topic) and to look up topic weights at ranking time. No LLM — cheap and
reproducible.
"""

from __future__ import annotations

from .config import prefilter_config
from .models import Finding


def topics_of(finding: Finding, keywords: list[str] | None = None) -> list[str]:
    if keywords is None:
        keywords = prefilter_config().get("keywords", [])
    text = f"{finding.title} {finding.summary or ''}".lower()
    return [k.lower() for k in keywords if k.lower() in text]
