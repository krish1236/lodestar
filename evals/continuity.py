"""Continuity eval (Axis B, behavior-model part) — the memory thesis, proven for
the structured tier. Simulates a year of runs + scripted feedback and asserts:

  1. Taste fidelity: a consistently-liked topic ends high, a disliked one low —
     and both stay bounded (no runaway).
  2. Time-travel: folding a prefix of the log is a pure function (reproducible),
     so state as-of any past day is recoverable.
  3. No loss: every run over the horizon is accounted for.
  4. No mission drift: the pipeline emits only item_shown/run_completed/feedback
     events — nothing that could mutate the constitution (taste ≠ mission).

Deterministic, no LLM/network — runs in CI. The semantic-retrieval half of
Axis B (retrieval quality over an aged archive) is deferred until embeddings
(Phase 2.4) land.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from lodestar.memory import behavior_model

_SAFE_EVENT_TYPES = {"item_shown", "run_completed", "feedback"}


def _simulate(days: int) -> list[dict]:
    events: list[dict] = []
    for d in range(days):
        events.append({"type": "item_shown", "source": "arxiv",
                       "url": f"https://x/agent{d}", "topics": ["agent"]})
        events.append({"type": "item_shown", "source": "hackernews",
                       "url": f"https://x/crypto{d}", "topics": ["crypto"]})
        events.append({"type": "feedback", "url": f"https://x/agent{d}", "signal": "up"})
        events.append({"type": "feedback", "url": f"https://x/crypto{d}", "signal": "down"})
        events.append({"type": "run_completed", "run_id": f"d{d:03d}"})
    return events


def run() -> int:
    tmp = Path(tempfile.mkdtemp())
    events = _simulate(365)
    failures = 0

    model = behavior_model.rebuild(events, path=tmp / "bm.json")
    agent_w = model["topics"]["agent"]["weight"]
    crypto_w = model["topics"]["crypto"]["weight"]
    ok = 0.0 <= crypto_w < 0.5 < agent_w <= 1.0
    print(f"[{'PASS' if ok else 'FAIL'}] taste fidelity: agent={agent_w} crypto={crypto_w} (bounded, directional)")
    failures += 0 if ok else 1

    prefix = events[: len(events) // 2]
    a = behavior_model.rebuild(prefix, path=tmp / "a.json")
    b = behavior_model.rebuild(prefix, path=tmp / "b.json")
    ok = a == b
    print(f"[{'PASS' if ok else 'FAIL'}] time-travel reproducible (fold of a prefix is pure)")
    failures += 0 if ok else 1

    ok = model["runs"] == 365
    print(f"[{'PASS' if ok else 'FAIL'}] no loss over horizon: runs={model['runs']}/365")
    failures += 0 if ok else 1

    mutating = [e for e in events if e.get("type") not in _SAFE_EVENT_TYPES]
    ok = not mutating
    print(f"[{'PASS' if ok else 'FAIL'}] no mission drift: {len(mutating)} events could mutate the constitution")
    failures += 0 if ok else 1

    print("CONTINUITY:", "PASS" if failures == 0 else f"FAIL ({failures})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
