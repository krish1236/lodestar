"""Entry point: build the graph and run one daily pass.

Run with `python -m lodestar.main` or the `lodestar` console script.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from .graph import build_graph
from .observability import write_metrics


def run() -> None:
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start = time.monotonic()
    graph = build_graph()
    final = graph.invoke({"run_date": run_date, "findings": [], "errors": []})
    metrics = write_metrics(run_date, final, time.monotonic() - start)

    errors = final.get("errors", [])
    print(
        f"[lodestar] {run_date}: fetched {metrics['fetched']}, "
        f"surfaced {metrics['surfaced']} item(s) in {metrics['duration_seconds']}s, "
        f"{len(errors)} source error(s)."
    )
    for e in errors:
        print(f"  ERROR [{e.source}]: {e.message}")


if __name__ == "__main__":
    run()
