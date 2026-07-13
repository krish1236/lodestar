"""Entry point: build the graph and run one daily pass.

Run with `python -m lodestar.main` or the `lodestar` console script.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .graph import build_graph


def run() -> None:
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    graph = build_graph()
    final = graph.invoke({"run_date": run_date, "findings": [], "errors": []})

    fetched = final.get("findings", [])
    surfaced = final.get("deduped", fetched)
    errors = final.get("errors", [])
    print(
        f"[lodestar] {run_date}: fetched {len(fetched)}, "
        f"surfaced {len(surfaced)} new item(s), {len(errors)} source error(s)."
    )
    for e in errors:
        print(f"  ERROR [{e.source}]: {e.message}")


if __name__ == "__main__":
    run()
