"""Behavior-model skeleton — the durable structured store.

Phase 1.7 records simple aggregates (runs, per-source surfaced counts). In v2
this becomes a materialized view over the event log with interest weights and
topic threads, folded by deterministic rules. Idempotent per day via
`last_run_id`.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import REPO_ROOT
from ..models import Finding

BM_PATH = REPO_ROOT / "state" / "behavior_model.json"
_DEFAULT = {"runs": 0, "by_source": {}, "topics": {}, "updated": None, "last_run_id": None}


def load(path: Path | None = None) -> dict:
    path = path or BM_PATH
    if not path.exists():
        return dict(_DEFAULT)
    return {**_DEFAULT, **json.loads(path.read_text(encoding="utf-8") or "{}")}


def save(model: dict, path: Path | None = None) -> None:
    path = path or BM_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update(surfaced: list[Finding], run_id: str, path: Path | None = None) -> dict:
    model = load(path)
    if model.get("last_run_id") == run_id:
        return model  # idempotent: same day re-run does not double-count
    model["runs"] = model.get("runs", 0) + 1
    by_source = model.setdefault("by_source", {})
    for f in surfaced:
        by_source[f.source] = by_source.get(f.source, 0) + 1
    model["updated"] = run_id
    model["last_run_id"] = run_id
    save(model, path)
    return model
