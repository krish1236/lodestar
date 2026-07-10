"""Render is pure and network-free — the kind of domain logic we keep testable
without the framework or live sources."""

from lodestar.digest import render
from lodestar.models import Finding
from lodestar.sources.base import SourceError


def _finding(**kw) -> Finding:
    base = dict(
        source="hackernews",
        external_id="1",
        url="https://example.com/x",
        title="A substantive thing",
        published_at="2026-01-01T00:00:00Z",
    )
    base.update(kw)
    return Finding(**base)


def test_render_includes_item_meta_and_why():
    md = render(
        [_finding(author="alice", credibility_signals={"points": 42}, why="matters because X")],
        "2026-01-01",
        [],
    )
    assert "A substantive thing" in md
    assert "https://example.com/x" in md
    assert "@alice" in md
    assert "42 pts" in md
    assert "matters because X" in md


def test_render_quiet_day():
    assert "Quiet day" in render([], "2026-01-01", [])


def test_render_surfaces_source_errors():
    md = render([], "2026-01-01", [SourceError("hackernews", "boom")])
    assert "hackernews" in md and "boom" in md
