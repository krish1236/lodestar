"""Judge-gating eval (Axis A) — labeled coverage scenarios over the judge's
deterministic path. Runs in CI (no LLM); exits non-zero on any mismatch.

The LLM judge path is nondeterministic and evaluated on-demand, not here.
"""

from __future__ import annotations

import sys

from lodestar import judge
from lodestar.sources.base import SourceError

KNOWN = {"arxiv", "github", "hackernews", "exa"}

SCENARIOS = [
    ("full coverage -> sufficient",
     {"arxiv": 12, "github": 4, "hackernews": 6}, [],
     {"sufficient": True, "gaps": []}),
    ("errored source -> gap",
     {"arxiv": 12}, [SourceError("github", "500")],
     {"sufficient": False, "gaps": ["github"]}),
    ("errored but recovered -> not a gap",
     {"arxiv": 12, "github": 3}, [],
     {"sufficient": True, "gaps": []}),
    ("empty run -> quiet day",
     {}, [],
     {"sufficient": True, "quiet_day": True, "gaps": []}),
]


def run() -> int:
    judge.ANTHROPIC_API_KEY = None  # force the deterministic path, CI-safe
    failures = 0
    for name, coverage, errors, expected in SCENARIOS:
        verdict = judge.assess(coverage, errors, KNOWN)
        ok = all(verdict.get(k) == v for k, v in expected.items())
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {verdict}")
        failures += 0 if ok else 1
    print("JUDGE-GATING:", "PASS" if failures == 0 else f"FAIL ({failures})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
