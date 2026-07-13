"""Dedup (seen-keys) and watermark logic — file-backed but isolated to tmp."""

from lodestar.memory import seen_keys, watermark
from lodestar.models import Finding


def _f(url: str, source: str = "hackernews", published_at: str = "2026-01-02T00:00:00Z") -> Finding:
    return Finding(
        source=source,
        external_id=url,
        url=url,
        title="t",
        published_at=published_at,
    )


def test_normalize_key_collapses_url_variants():
    a = seen_keys.normalize_key(_f("https://Example.com/Post/"))
    b = seen_keys.normalize_key(_f("https://example.com/Post?utm_source=x#frag"))
    assert a == b  # host-case, trailing slash, query, fragment all normalized away


def test_filter_new_drops_seen_and_within_run_dupes():
    seen = {seen_keys.normalize_key(_f("https://example.com/old"))}
    findings = [
        _f("https://example.com/old"),  # already seen
        _f("https://example.com/new"),  # fresh
        _f("https://example.com/new"),  # within-run dup of the previous
    ]
    fresh = seen_keys.filter_new(findings, seen)
    assert [f.url for f in fresh] == ["https://example.com/new"]


def test_seen_keys_persist_and_dedup_on_reload(tmp_path, monkeypatch):
    path = tmp_path / "seen.txt"
    monkeypatch.setattr(seen_keys, "SEEN_PATH", path)
    first = seen_keys.filter_new([_f("https://example.com/a")], seen_keys.load())
    seen_keys.append(first)
    # Second run, same item -> nothing fresh.
    second = seen_keys.filter_new([_f("https://example.com/a")], seen_keys.load())
    assert first and not second


def test_watermark_filters_older_and_advances():
    wm = {"hackernews": "2026-01-02T00:00:00+00:00"}
    older = _f("https://example.com/old", published_at="2026-01-01T00:00:00Z")
    newer = _f("https://example.com/new", published_at="2026-01-03T00:00:00Z")
    kept = watermark.filter_newer([older, newer], wm)
    assert [f.url for f in kept] == ["https://example.com/new"]
    advanced = watermark.advance([older, newer], wm)
    assert advanced["hackernews"].startswith("2026-01-03")
