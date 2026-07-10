"""Phase 0 entry point: the whole thin slice, end to end.

    load constitution -> fetch HN -> add "why" -> render -> write files

Run with `python -m lodestar.main` or the `lodestar` console script.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .config import load_constitution
from .digest import render, write_digest
from .sources.hackernews import HackerNewsAdapter

# Small cap for the skeleton — one source, a handful of front-page items.
CAP = 10


def run() -> None:
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    constitution = load_constitution()

    result = HackerNewsAdapter().fetch(CAP)
    from .synthesize import add_why

    findings = add_why(result.findings, constitution)

    markdown = render(findings, run_date, result.errors)
    write_digest(markdown, run_date)

    print(
        f"[lodestar] {run_date}: wrote {len(findings)} item(s), "
        f"{len(result.errors)} source error(s)."
    )
    for e in result.errors:
        print(f"  ERROR [{e.source}]: {e.message}")


if __name__ == "__main__":
    run()
