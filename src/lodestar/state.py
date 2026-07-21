"""The graph's working state — ephemeral, per-run.

Only fan-out-target keys carry reducers: when parallel source branches (Phase
1.2) write `findings`/`errors` in the same superstep, `operator.add` concatenates
them instead of clobbering. Single-writer keys (constitution, digest_md) need no
reducer. Downstream logic must not depend on fan-in order — dedup is set-based
and ranking sorts by score.

Durable memory (event log, seen-keys, behavior model) lives in separate stores,
not here; RunState stays small and is discarded at run end.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from .models import Finding
from .sources.base import SourceError


class RunState(TypedDict, total=False):
    run_date: str
    constitution: str
    findings: Annotated[list[Finding], operator.add]  # fan-out target -> reducer
    errors: Annotated[list[SourceError], operator.add]  # fan-out target -> reducer
    deduped: list[Finding]  # single writer (dedup/prefilter) — the considered set
    verified: list[Finding]  # single writer (verify) — survivors of reachability+substance
    surfaced: list[Finding]  # single writer (synthesize) — the ranked items in the digest
    digest_md: str  # single writer (synthesize)
