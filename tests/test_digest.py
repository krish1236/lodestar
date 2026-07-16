"""Sectioned render is pure and network-free."""

from lodestar.digest import render
from lodestar.models import Finding
from lodestar.sources.base import SourceError


def _f(**kw) -> Finding:
    base = dict(
        source="hackernews",
        external_id="1",
        url="https://example.com/x",
        title="A substantive thing",
        published_at="2026-01-01T00:00:00Z",
    )
    base.update(kw)
    return Finding(**base)


def test_render_overview_highlights_sections_and_meta():
    f = _f(author="alice", credibility_signals={"points": 42, "trusted": True}, why="because X")
    md = render("2026-01-01", "today's theme", [f], {"Discussion": [f]}, {"hackernews": 1}, [])
    assert "today's theme" in md
    assert "## Highlights" in md and "## Discussion" in md
    assert "A substantive thing" in md
    assert "@alice" in md and "42 pts" in md and "trusted" in md
    assert "because X" in md


def test_render_quiet_day():
    assert "Quiet day" in render("2026-01-01", None, [], {}, {}, [])


def test_render_coverage_line_distinguishes_quiet_from_broken():
    md = render("2026-01-01", None, [], {}, {"arxiv": 12, "github": 4}, [])
    assert "Coverage:" in md and "arxiv 12" in md


def test_render_surfaces_source_errors():
    md = render("2026-01-01", None, [], {}, {}, [SourceError("hackernews", "boom")])
    assert "hackernews" in md and "boom" in md
