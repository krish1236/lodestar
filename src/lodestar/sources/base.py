"""The source seam.

Every source implements `SourceAdapter.fetch()` and returns a `FetchResult`.
Adapters are *fault-isolated*: a source outage returns an error in the result
rather than raising, so one flaky API degrades the digest gracefully instead of
aborting the whole run.

Note: `fetch` takes only `cap` for now; the per-source watermark (incremental
"what's new since last run") arrives in Phase 1.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..models import Finding


@dataclass
class SourceError:
    source: str
    message: str


@dataclass
class FetchResult:
    findings: list[Finding]
    errors: list[SourceError] = field(default_factory=list)


class SourceAdapter(Protocol):
    name: str

    def fetch(self, cap: int) -> FetchResult:
        """Return up to `cap` candidate findings. Never raises — errors are
        returned in `FetchResult.errors`."""
        ...
