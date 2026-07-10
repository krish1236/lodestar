"""The graph shell wires together and runs, with the pass-through nodes intact.

Sources are monkeypatched to avoid network; this checks graph *structure and
flow*, not live fetching.
"""

from lodestar import graph as g
from lodestar.models import Finding
from lodestar.sources.base import FetchResult


def test_graph_runs_end_to_end(monkeypatch, tmp_path):
    fake = Finding(
        source="hackernews",
        external_id="1",
        url="https://example.com/x",
        title="A substantive thing",
        published_at="2026-01-01T00:00:00Z",
        credibility_signals={"points": 99},
    )

    # No network, no LLM, no disk writes outside tmp.
    monkeypatch.setattr(
        g.HackerNewsAdapter, "fetch", lambda self, cap: FetchResult(findings=[fake])
    )
    monkeypatch.setattr(g, "load_constitution", lambda: "mission")
    monkeypatch.setattr(g, "add_why", lambda findings, constitution: findings)
    written = {}
    monkeypatch.setattr(g, "write_digest", lambda md, date: written.update(md=md, date=date))

    final = g.build_graph().invoke({"run_date": "2026-01-01", "findings": [], "errors": []})

    assert len(final["findings"]) == 1
    assert "A substantive thing" in written["md"]
    assert written["date"] == "2026-01-01"
