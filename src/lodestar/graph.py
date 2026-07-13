"""The LangGraph pipeline assembly.

Spine:  load_context -> [gather_* fan-out] -> dedup -> verify -> judge
                     -> synthesize -> consolidate

`gather` is now a real **fan-out**: one node per source, all dispatched in the
same superstep, their findings merged by the `operator.add` reducer on
`RunState.findings` (Phase 5 concurrency design). `dedup`, `verify`, and `judge`
remain pass-through nodes so later phases are additive.

LangGraph is confined to this file; nodes call plain-Python domain logic.
No checkpointer — a daily run is short and idempotent (deferred, per design).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .config import (
    arxiv_config,
    exa_config,
    github_watchlist,
    load_constitution,
    prefilter_config,
)
from .credibility import mark_trusted
from .digest import render, write_digest
from .memory import seen_keys, watermark
from .prefilter import prefilter
from .sources.arxiv import ArxivAdapter
from .sources.base import SourceAdapter
from .sources.exa import ExaAdapter
from .sources.github import GitHubAdapter
from .sources.hackernews import HackerNewsAdapter
from .state import RunState
from .synthesize import add_why

# Per-source candidate caps (Phase 1.4 refines the cheap pre-filter for arXiv).
_DEFAULT_CAP = 10


def _adapters() -> list[tuple[SourceAdapter, int]]:
    """Build the source adapters from config. Returns (adapter, cap) pairs."""
    ax = arxiv_config()
    exa = exa_config()
    return [
        (HackerNewsAdapter(), _DEFAULT_CAP),
        (ArxivAdapter(ax["categories"], ax.get("cap", 15)), ax.get("cap", 15)),
        (GitHubAdapter(github_watchlist()), _DEFAULT_CAP),
        (ExaAdapter(exa.get("query", ""), exa.get("domains", [])), _DEFAULT_CAP),
    ]


def _make_gather(adapter: SourceAdapter, cap: int):
    def _node(state: RunState) -> dict:
        result = adapter.fetch(cap)
        findings = mark_trusted(result.findings)  # derived allowlist signal
        return {"findings": findings, "errors": result.errors}

    _node.__name__ = f"gather_{adapter.name}"
    return _node


def load_context(state: RunState) -> dict:
    return {"constitution": load_constitution()}


def dedup(state: RunState) -> dict:
    # Watermark (efficiency) then seen-keys (correctness). Writes the reduced
    # set to `deduped` — it must NOT return `findings`, which is reducer-backed
    # and would append rather than replace.
    raw = state.get("findings", [])
    fresh = watermark.filter_newer(raw, watermark.load())
    deduped = seen_keys.filter_new(fresh, seen_keys.load())
    return {"deduped": deduped}


def prefilter_node(state: RunState) -> dict:
    # Cheap keyword/recency filter + per-source caps before the LLM stages.
    # Overwrites `deduped` (single-writer key, safe to replace).
    kept = prefilter(state.get("deduped", []), prefilter_config())
    return {"deduped": kept}


def verify(state: RunState) -> dict:
    return {}  # pass-through — adversarial verifier in Phase 2.1


def judge(state: RunState) -> dict:
    return {}  # pass-through — sufficiency loop + conditional edge in Phase 2.2


def synthesize(state: RunState) -> dict:
    findings = add_why(state.get("deduped", []), state.get("constitution", ""))
    markdown = render(findings, state["run_date"], state.get("errors", []))
    return {"digest_md": markdown}


def consolidate(state: RunState) -> dict:
    write_digest(state["digest_md"], state["run_date"])
    # Persist durable state: mark surfaced items seen, advance watermarks from
    # everything fetched. (Phase 1.7 also emits events here.)
    deduped = state.get("deduped", [])
    seen_keys.append(deduped)
    watermark.save(watermark.advance(state.get("findings", []), watermark.load()))
    return {}


def build_graph():
    g = StateGraph(RunState)
    g.add_node("load_context", load_context)

    adapters = _adapters()
    for adapter, cap in adapters:
        g.add_node(f"gather_{adapter.name}", _make_gather(adapter, cap))

    for name, fn in [
        ("dedup", dedup),
        ("prefilter", prefilter_node),
        ("verify", verify),
        ("judge", judge),
        ("synthesize", synthesize),
        ("consolidate", consolidate),
    ]:
        g.add_node(name, fn)

    g.add_edge(START, "load_context")
    for adapter, _ in adapters:
        g.add_edge("load_context", f"gather_{adapter.name}")  # fan-out
        g.add_edge(f"gather_{adapter.name}", "dedup")  # fan-in (reducer merges)

    g.add_edge("dedup", "prefilter")
    g.add_edge("prefilter", "verify")
    g.add_edge("verify", "judge")
    g.add_edge("judge", "synthesize")  # Phase 2.2 makes this a conditional edge
    g.add_edge("synthesize", "consolidate")
    g.add_edge("consolidate", END)
    return g.compile()
