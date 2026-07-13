"""The cheap pre-filter: keyword relevance for volume sources, caps, pass-through
for curated sources."""

from lodestar.models import Finding
from lodestar.prefilter import prefilter

CFG = {
    "filtered_sources": ["arxiv", "hackernews"],
    "keywords": ["agent", "llm"],
    "caps": {"arxiv": 2, "github": 5},
}


def _f(source: str, title: str) -> Finding:
    return Finding(source=source, external_id=title, url="https://x/" + title, title=title,
                   published_at="2026-01-01")


def test_keyword_filter_drops_off_mission_volume_sources():
    kept = prefilter(
        [_f("hackernews", "A new LLM agent framework"), _f("hackernews", "Best train sim ever")],
        CFG,
    )
    assert [f.title for f in kept] == ["A new LLM agent framework"]


def test_curated_sources_bypass_keyword_filter():
    kept = prefilter([_f("github", "owner/repo v1.0")], CFG)  # no keyword, but curated
    assert len(kept) == 1


def test_per_source_cap_applies():
    items = [_f("arxiv", f"agent paper {i}") for i in range(5)]
    kept = prefilter(items, CFG)
    assert len(kept) == 2  # arxiv cap
