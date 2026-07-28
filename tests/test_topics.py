"""Deterministic topic tagging."""

from lodestar.models import Finding
from lodestar.topics import topics_of

KW = ["agent", "llm", "rag"]


def _f(title: str, summary: str = "") -> Finding:
    return Finding(source="x", external_id="1", url="https://x", title=title,
                   published_at="2026-01-01", summary=summary)


def test_topics_match_keywords_case_insensitive():
    assert set(topics_of(_f("An LLM Agent framework"), KW)) == {"agent", "llm"}


def test_topics_empty_when_no_match():
    assert topics_of(_f("A train simulator"), KW) == []
