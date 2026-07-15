"""Event log and behavior-model skeleton — file-backed, isolated to tmp."""

from lodestar.memory import behavior_model, events
from lodestar.models import Finding


def _f(ext: str) -> Finding:
    return Finding(source="arxiv", external_id=ext, url="https://x/" + ext, title="t",
                   published_at="2026-01-01", rank_score=1.0)


def test_emit_run_writes_item_and_run_events(tmp_path):
    path = tmp_path / "events.jsonl"
    events.emit_run("2026-01-01", [_f("a"), _f("b")], fetched=10, errors=0, path=path)
    log = events.load(path)
    kinds = [e["type"] for e in log]
    assert kinds.count("item_shown") == 2
    assert kinds.count("run_completed") == 1


def test_emit_run_is_idempotent_per_run(tmp_path):
    path = tmp_path / "events.jsonl"
    events.emit_run("2026-01-01", [_f("a")], 5, 0, path=path)
    events.emit_run("2026-01-01", [_f("a")], 5, 0, path=path)  # re-run
    log = events.load(path)
    assert [e["type"] for e in log].count("run_completed") == 1
    assert [e["type"] for e in log].count("item_shown") == 1


def test_behavior_model_aggregates_and_is_idempotent(tmp_path):
    path = tmp_path / "bm.json"
    behavior_model.update([_f("a"), _f("b")], "2026-01-01", path=path)
    behavior_model.update([_f("c")], "2026-01-01", path=path)  # same day -> no double count
    model = behavior_model.load(path)
    assert model["runs"] == 1
    assert model["by_source"]["arxiv"] == 2
