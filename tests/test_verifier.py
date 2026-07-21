"""Verifier survivor logic — reachability and substance monkeypatched (no net/LLM)."""

from lodestar import verifier
from lodestar.models import Finding


def _f(url: str, title: str = "t") -> Finding:
    return Finding(source="hackernews", external_id=url, url=url, title=title,
                   published_at="2026-01-01")


def test_verify_drops_unreachable(monkeypatch):
    monkeypatch.setattr(verifier, "ANTHROPIC_API_KEY", None)  # skip substance
    monkeypatch.setattr(verifier, "_reachable", lambda url: "live" in url)
    out = verifier.verify([_f("https://live/a"), _f("https://dead/b")])
    assert [f.url for f in out] == ["https://live/a"]


def test_verify_drops_hype_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")  # lets Anthropic() construct
    monkeypatch.setattr(verifier, "ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(verifier, "_reachable", lambda url: True)
    monkeypatch.setattr(verifier, "_substantive", lambda f, client: "hype" not in f.title.lower())
    out = verifier.verify([_f("https://x/a", "A real technique"), _f("https://x/b", "hype 10x magic")])
    assert [f.title for f in out] == ["A real technique"]


def test_verify_empty():
    assert verifier.verify([]) == []
