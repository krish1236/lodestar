"""No-repeat eval — the cleanest, truest metric we have (Topic 11, Axis A).

Two deterministic checks over the committed state:
  1. seen-keys has no duplicate lines (the never-lossy index stays clean).
  2. no item_shown URL appears in more than one run (never surfaced twice).

Exits non-zero on failure so CI fails a regression in the no-repeat guarantee.
"""

from __future__ import annotations

import sys
from collections import defaultdict

from lodestar.memory import events
from lodestar.memory.seen_keys import SEEN_PATH


def run() -> int:
    lines = SEEN_PATH.read_text(encoding="utf-8").splitlines() if SEEN_PATH.exists() else []
    keys = [ln.strip() for ln in lines if ln.strip()]
    dupes = len(keys) - len(set(keys))

    runs_by_url: dict[str, set[str]] = defaultdict(set)
    shown = 0
    for e in events.load():
        if e.get("type") == "item_shown":
            shown += 1
            runs_by_url[e.get("url")].add(e.get("run_id"))
    repeated = sum(1 for r in runs_by_url.values() if len(r) > 1)

    print(f"seen-keys: {len(keys)} keys, {dupes} duplicate(s)")
    print(f"events:    {shown} item_shown across {len({r for rs in runs_by_url.values() for r in rs})} run(s), "
          f"{repeated} URL(s) surfaced in >1 run")
    ok = dupes == 0 and repeated == 0
    print("NO-REPEAT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
