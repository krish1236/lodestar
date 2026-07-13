"""Ranking formula: credibility as a bounded booster, relevance as the gate,
highlights on the universal axis, sections like-with-like."""

from lodestar.models import Finding
from lodestar.ranking import build_sections, credibility_boost, rank


def _f(source: str, relevance: float, signals: dict | None = None) -> Finding:
    return Finding(source=source, external_id="x", url="https://x/" + source, title="t",
                   published_at="2026-01-01", relevance=relevance, credibility_signals=signals or {})


def test_credibility_boost_is_bounded_and_never_below_one():
    assert credibility_boost({}) == 1.0  # unknown author -> no penalty
    assert 1.0 < credibility_boost({"trusted": True}) <= 2.0
    assert credibility_boost({"trusted": True, "stars": 10**9, "karma": 10**9}) <= 2.0  # capped


def test_rank_drops_off_mission_and_scores_survivors():
    kept = rank([_f("hackernews", 0.1), _f("arxiv", 0.8)])
    assert [f.source for f in kept] == ["arxiv"]
    assert kept[0].rank_score is not None


def test_highlights_by_relevance_sections_present():
    ranked = rank([
        _f("arxiv", 0.9),
        _f("github", 0.5, {"stars": 30000}),
        _f("hackernews", 0.7),
    ])
    highlights, sections = build_sections(ranked, n_highlights=2)
    assert len(highlights) == 2
    assert highlights[0].relevance == 0.9  # chosen on the universal axis
    assert set(sections) == {"Papers", "Releases", "Discussion"}
