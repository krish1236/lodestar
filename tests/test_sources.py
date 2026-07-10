"""Network-free parsing tests for the source adapters.

Each adapter separates pure parsing from network I/O, so we test the parsing on
fixtures without hitting live APIs.
"""

from lodestar.sources import arxiv, exa, github
from lodestar.sources.exa import ExaAdapter

_ARXIV_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:arxiv="http://arxiv.org/schemas/atom"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <item>
    <title>A New Agent Framework</title>
    <link>https://arxiv.org/abs/2501.00001</link>
    <description>Abstract: something substantive.</description>
    <dc:creator>Jane Doe, John Smith</dc:creator>
    <arxiv:announce_type>new</arxiv:announce_type>
  </item>
  <item>
    <title>A Replaced Paper</title>
    <link>https://arxiv.org/abs/2412.99999</link>
    <dc:creator>Someone Else</dc:creator>
    <arxiv:announce_type>replace</arxiv:announce_type>
  </item>
</channel>
</rss>"""


def test_arxiv_keeps_only_new_announcements():
    findings = arxiv.parse(_ARXIV_RSS, cap=10)
    assert len(findings) == 1
    assert findings[0].title == "A New Agent Framework"
    assert findings[0].source == "arxiv"


def test_github_parse_skips_drafts_and_builds_title():
    releases = [
        {"tag_name": "v1.0", "name": "Shiny", "html_url": "https://gh/x",
         "published_at": "2026-01-01", "author": {"login": "octocat"}, "draft": False},
        {"tag_name": "v0.9", "draft": True},
    ]
    findings = github.parse("owner/repo", releases)
    assert len(findings) == 1
    assert findings[0].title == "owner/repo Shiny"
    assert findings[0].author == "octocat"


def test_exa_parse_maps_results():
    results = [{"id": "1", "url": "https://x", "title": "Thing", "publishedDate": "2026-01-01"}]
    findings = exa.parse(results)
    assert findings[0].url == "https://x"
    assert findings[0].source == "exa"


def test_exa_adapter_no_key_is_silent(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    result = ExaAdapter("q", ["example.com"]).fetch(cap=5)
    assert result.findings == [] and result.errors == []
