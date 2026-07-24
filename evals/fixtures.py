"""FixtureAdapter — a SourceAdapter backed by a fixed corpus.

This is the seam that makes evaluation reproducible (Topic 11): the same
pipeline that runs against the live web runs against fixtures with no other code
change. Live web for the product, fixed corpus for the eval.
"""

from __future__ import annotations

from lodestar.models import Finding
from lodestar.sources.base import FetchResult


class FixtureAdapter:
    def __init__(self, name: str, findings: list[Finding]):
        self.name = name
        self._findings = findings

    def fetch(self, cap: int) -> FetchResult:
        return FetchResult(findings=list(self._findings)[:cap])


def sample_corpus() -> list[Finding]:
    """A small, labeled corpus spanning all sections."""
    return [
        Finding(
            source="arxiv", external_id="p1", url="https://arxiv.org/abs/2601.00001",
            title="A graph-augmented planner for LLM agents",
            published_at="2026-01-02T00:00:00Z", summary="agent planning",
        ),
        Finding(
            source="github", external_id="langchain-ai/langgraph@v9", url="https://github.com/langchain-ai/langgraph/releases/tag/v9",
            title="langchain-ai/langgraph v9", published_at="2026-01-02T00:00:00Z",
            credibility_signals={"stars": 40000, "owner_login": "langchain-ai", "trusted": True},
        ),
        Finding(
            source="hackernews", external_id="h1", url="https://news.ycombinator.com/item?id=1",
            title="Show HN: an eval harness for agents", published_at="2026-01-02T00:00:00Z",
            credibility_signals={"points": 240, "karma": 6000},
        ),
    ]
