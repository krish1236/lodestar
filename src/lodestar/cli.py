"""Small CLIs. `lodestar-feedback <url> up|down` records a thumbs-up/down as a
feedback event; the next run folds it into the behavior model's topic weights
(taste evolves — never the constitution)."""

from __future__ import annotations

import sys

from .memory import events

_UP = {"up", "+1", "y", "yes"}
_DOWN = {"down", "-1", "n", "no"}


def feedback() -> None:
    args = sys.argv[1:]
    if len(args) < 2 or (args[1].lower() not in _UP and args[1].lower() not in _DOWN):
        print("usage: lodestar-feedback <url> up|down")
        sys.exit(2)
    url = args[0]
    signal = "up" if args[1].lower() in _UP else "down"
    events.emit_feedback(url, signal)
    print(f"recorded {signal} for {url}")
