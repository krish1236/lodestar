"""The LangGraph pipeline assembly.

Spine:  load_context -> gather -> dedup -> verify -> judge -> synthesize -> consolidate

`dedup`, `verify`, and `judge` are deliberate **pass-through nodes** in this
phase. Reserving them now means later phases (real dedup in 1.3, the verifier in
2.1, the judged loop in 2.2) are additive edits — the graph shape doesn't change.

LangGraph is confined to this file: nodes call plain-Python domain logic
(sources, synthesize, digest) and never leak framework types into it.
No checkpointer — a daily run is short and idempotent (deferred, per design).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .config import load_constitution
from .digest import render, write_digest
from .sources.hackernews import HackerNewsAdapter
from .state import RunState
from .synthesize import add_why

# Per-source candidate cap (Phase 1.4 makes this per-source config).
CAP = 10


def load_context(state: RunState) -> dict:
    return {"constitution": load_constitution()}


def gather(state: RunState) -> dict:
    # Phase 1.2 replaces this single node with a parallel fan-out over adapters;
    # the `findings`/`errors` reducers are already in place for that.
    result = HackerNewsAdapter().fetch(CAP)
    return {"findings": result.findings, "errors": result.errors}


def dedup(state: RunState) -> dict:
    return {}  # pass-through — real exact/semantic dedup in Phase 1.3


def verify(state: RunState) -> dict:
    return {}  # pass-through — adversarial verifier in Phase 2.1


def judge(state: RunState) -> dict:
    return {}  # pass-through — sufficiency loop + conditional edge in Phase 2.2


def synthesize(state: RunState) -> dict:
    findings = add_why(state.get("findings", []), state.get("constitution", ""))
    markdown = render(findings, state["run_date"], state.get("errors", []))
    return {"digest_md": markdown}


def consolidate(state: RunState) -> dict:
    write_digest(state["digest_md"], state["run_date"])
    return {}  # Phase 1.7 emits events + updates seen-keys here


def build_graph():
    g = StateGraph(RunState)
    for name, fn in [
        ("load_context", load_context),
        ("gather", gather),
        ("dedup", dedup),
        ("verify", verify),
        ("judge", judge),
        ("synthesize", synthesize),
        ("consolidate", consolidate),
    ]:
        g.add_node(name, fn)

    g.add_edge(START, "load_context")
    g.add_edge("load_context", "gather")
    g.add_edge("gather", "dedup")
    g.add_edge("dedup", "verify")
    g.add_edge("verify", "judge")
    g.add_edge("judge", "synthesize")  # Phase 2.2 makes this a conditional edge
    g.add_edge("synthesize", "consolidate")
    g.add_edge("consolidate", END)
    return g.compile()
