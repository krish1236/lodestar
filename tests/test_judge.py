"""Judge verdicts: deterministic path, parsing, and the errored-source rule."""

from lodestar import judge
from lodestar.sources.base import SourceError

KNOWN = {"arxiv", "github", "hackernews", "exa"}


def test_no_key_all_covered_is_sufficient(monkeypatch):
    monkeypatch.setattr(judge, "ANTHROPIC_API_KEY", None)
    v = judge.assess({"arxiv": 12, "github": 4}, [], KNOWN)
    assert v["sufficient"] is True and v["gaps"] == []


def test_no_key_errored_source_becomes_a_gap(monkeypatch):
    monkeypatch.setattr(judge, "ANTHROPIC_API_KEY", None)
    v = judge.assess({"arxiv": 12}, [SourceError("github", "500")], KNOWN)
    assert v["sufficient"] is False and v["gaps"] == ["github"]


def test_no_key_empty_run_is_a_quiet_day(monkeypatch):
    monkeypatch.setattr(judge, "ANTHROPIC_API_KEY", None)
    v = judge.assess({}, [], KNOWN)
    assert v["quiet_day"] is True and v["sufficient"] is True


def test_parse_structured_verdict_filters_unknown_sources():
    text = "SUFFICIENT: NO\nQUIET_DAY: NO\nGAPS: arxiv, nonsense\nREASON: papers thin"
    v = judge._parse(text, KNOWN)
    assert v["sufficient"] is False
    assert v["gaps"] == ["arxiv"]  # unknown source dropped
    assert v["reason"] == "papers thin"


def test_parse_quiet_day_sufficient():
    v = judge._parse("SUFFICIENT: YES\nQUIET_DAY: YES\nGAPS: NONE\nREASON: quiet", KNOWN)
    assert v["sufficient"] and v["quiet_day"] and v["gaps"] == []
