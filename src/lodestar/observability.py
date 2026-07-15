"""Per-run metrics — committed to runs/YYYY-MM-DD.json as versioned history.

Records coverage (per-source surfaced counts), fetched/surfaced totals, source
errors, and wall-clock duration. Token/cost accounting is added when the LLM
calls thread usage through (later phase).
"""

from __future__ import annotations

import json
from collections import Counter

from .config import REPO_ROOT


def write_metrics(run_date: str, final_state: dict, duration_seconds: float) -> dict:
    surfaced = final_state.get("surfaced", [])
    errors = final_state.get("errors", [])
    metrics = {
        "run_date": run_date,
        "fetched": len(final_state.get("findings", [])),
        "surfaced": len(surfaced),
        "by_source": dict(Counter(f.source for f in surfaced)),
        "errors": [{"source": e.source, "message": e.message} for e in errors],
        "duration_seconds": round(duration_seconds, 2),
    }
    runs_dir = REPO_ROOT / "runs"
    runs_dir.mkdir(exist_ok=True)
    (runs_dir / f"{run_date}.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metrics
