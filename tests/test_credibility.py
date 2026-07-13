"""Trust marking (allowlist) and GitHub signal attachment — network-free."""

from lodestar.credibility import mark_trusted
from lodestar.models import Finding
from lodestar.sources import github

ALLOW = {"orgs": ["anthropics"], "domains": ["anthropic.com"], "authors": ["karpathy"]}


def _f(url: str, source: str = "exa", author: str | None = None, signals: dict | None = None):
    return Finding(source=source, external_id=url, url=url, title="t", published_at="2026-01-01",
                   author=author, credibility_signals=signals or {})


def test_trusted_by_github_org():
    f = _f("https://github.com/anthropics/x", source="github", signals={"owner_login": "anthropics"})
    mark_trusted([f], ALLOW)
    assert f.credibility_signals["trusted"] is True


def test_trusted_by_domain_including_subdomain():
    f = _f("https://www.anthropic.com/news/x")
    mark_trusted([f], ALLOW)
    assert f.credibility_signals["trusted"] is True


def test_untrusted_unknown_source():
    f = _f("https://randomblog.example/post")
    mark_trusted([f], ALLOW)
    assert f.credibility_signals["trusted"] is False


def test_github_parse_attaches_repo_meta():
    releases = [{"tag_name": "v1", "html_url": "https://gh/x", "published_at": "2026-01-01",
                 "author": {"login": "bot"}, "draft": False}]
    meta = {"stars": 12000, "owner_type": "Organization", "owner_login": "langchain-ai"}
    findings = github.parse("langchain-ai/langgraph", releases, meta)
    assert findings[0].credibility_signals["stars"] == 12000
    assert findings[0].credibility_signals["owner_type"] == "Organization"
