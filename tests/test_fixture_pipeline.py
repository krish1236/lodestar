"""The fixture seam: the full graph runs against a fixed corpus, reproducibly.

Network/LLM stages are stubbed (they are evaluated separately, on-demand), so
this asserts the deterministic spine — sectioning and stable ordering — which is
what the reproducible eval relies on.
"""

from evals.fixtures import FixtureAdapter, sample_corpus
from lodestar import graph as g
from lodestar import judge
from lodestar.memory import behavior_model, events, seen_keys, watermark


def _run(monkeypatch, tmp_path) -> dict:
    def _score(findings, constitution):
        for f in findings:
            f.relevance = 0.9
        return findings

    monkeypatch.setattr(g, "_adapters", lambda: [(FixtureAdapter("fixture", sample_corpus()), 10)])
    monkeypatch.setattr(g, "verify_items", lambda findings: findings)
    monkeypatch.setattr(g, "score_relevance", _score)
    monkeypatch.setattr(g, "overview", lambda h, c: None)
    monkeypatch.setattr(g, "write_digest", lambda md, date: None)
    monkeypatch.setattr(judge, "ANTHROPIC_API_KEY", None)
    monkeypatch.setattr(seen_keys, "SEEN_PATH", tmp_path / "s.txt")
    monkeypatch.setattr(watermark, "WM_PATH", tmp_path / "w.json")
    monkeypatch.setattr(events, "EVENTS_PATH", tmp_path / "e.jsonl")
    monkeypatch.setattr(behavior_model, "BM_PATH", tmp_path / "b.json")
    return g.build_graph().invoke(
        {"run_date": "2026-01-02", "findings": [], "errors": [], "iteration": 0}
    )


def test_fixture_pipeline_sections_all_kinds(monkeypatch, tmp_path):
    final = _run(monkeypatch, tmp_path)
    sources = {f.source for f in final["surfaced"]}
    assert sources == {"arxiv", "github", "hackernews"}
    assert final["verdict"]["sufficient"] is True


def test_fixture_pipeline_is_reproducible(monkeypatch, tmp_path):
    a = _run(monkeypatch, tmp_path / "a")
    b = _run(monkeypatch, tmp_path / "b")
    assert [f.url for f in a["surfaced"]] == [f.url for f in b["surfaced"]]
