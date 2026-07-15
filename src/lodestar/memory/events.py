"""Append-only event log — the source of truth for change.

Phase 1.7 emits `item_shown` (per surfaced item) and `run_completed` (per run).
The behavior model becomes a materialized view over this log in v2; for now we
just start recording, so the history exists before we act on it.

Idempotent by construction: `item_shown` is keyed on (run_id, external_id) and
`run_completed` on run_id, so re-running a day never duplicates events.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import REPO_ROOT
from ..models import Finding

EVENTS_PATH = REPO_ROOT / "state" / "events.jsonl"


def load(path: Path | None = None) -> list[dict]:
    path = path or EVENTS_PATH
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(records: list[dict], path: Path) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def emit_run(
    run_id: str,
    surfaced: list[Finding],
    fetched: int,
    errors: int,
    path: Path | None = None,
) -> None:
    path = path or EVENTS_PATH
    existing = load(path)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    shown = {(e.get("run_id"), e.get("external_id")) for e in existing if e.get("type") == "item_shown"}
    have_run = any(e.get("type") == "run_completed" and e.get("run_id") == run_id for e in existing)

    records: list[dict] = []
    for f in surfaced:
        if (run_id, f.external_id) in shown:
            continue
        records.append({
            "ts": ts, "type": "item_shown", "run_id": run_id,
            "source": f.source, "external_id": f.external_id, "url": f.url,
            "rank_score": f.rank_score,
        })
    if not have_run:
        records.append({
            "ts": ts, "type": "run_completed", "run_id": run_id,
            "surfaced": len(surfaced), "fetched": fetched, "errors": errors,
        })
    _append(records, path)
