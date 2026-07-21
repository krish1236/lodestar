"""The graph shell wires together and runs, with the pass-through nodes intact.

The adapter registry is patched to a single fake source so the test is
network-free and checks graph *structure and flow*, not live fetching.
"""

from lodestar import graph as g
from lodestar.memory import behavior_model, events, seen_keys, watermark
from lodestar.models import Finding
from lodestar.sources.base import FetchResult


class _FakeAdapter:
    name = "fake"

    def __init__(self, finding: Finding):
        self._finding = finding

    def fetch(self, cap: int) -> FetchResult:
        return FetchResult(findings=[self._finding])


def test_graph_runs_end_to_end(monkeypatch, tmp_path):
    fake = Finding(
        source="fake",
        external_id="1",
        url="https://example.com/x",
        title="A substantive thing",
        published_at="2026-01-01T00:00:00Z",
        credibility_signals={"points": 99},
    )

    # One fake source; no network, no LLM, state isolated to tmp.
    def _fake_score(findings, constitution):
        for f in findings:
            f.relevance = 0.9
        return findings

    monkeypatch.setattr(g, "_adapters", lambda: [(_FakeAdapter(fake), 5)])
    monkeypatch.setattr(seen_keys, "SEEN_PATH", tmp_path / "seen.txt")
    monkeypatch.setattr(watermark, "WM_PATH", tmp_path / "wm.json")
    monkeypatch.setattr(events, "EVENTS_PATH", tmp_path / "events.jsonl")
    monkeypatch.setattr(behavior_model, "BM_PATH", tmp_path / "bm.json")
    monkeypatch.setattr(g, "load_constitution", lambda: "mission")
    monkeypatch.setattr(g, "verify_items", lambda findings: findings)  # no net/LLM
    monkeypatch.setattr(g, "score_relevance", _fake_score)
    monkeypatch.setattr(g, "overview", lambda highlights, constitution: None)
    written: dict = {}
    monkeypatch.setattr(g, "write_digest", lambda md, date: written.update(md=md, date=date))

    final = g.build_graph().invoke({"run_date": "2026-01-01", "findings": [], "errors": []})

    assert len(final["findings"]) == 1
    assert "A substantive thing" in written["md"]
    assert written["date"] == "2026-01-01"
