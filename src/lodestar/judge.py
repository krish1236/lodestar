"""Sufficiency gate (Phase 2.2) — the only LLM in the control loop.

Judges **coverage of the sweep**, not the size of the harvest: a quiet day with
two good items is a complete digest, not a failure. Only a source that errored
or is clearly under-swept counts as a gap. Errored sources are *always* gaps
(deterministic), and the LLM may add thin ones on top.

Emits a structured verdict; the router (deterministic, in graph.py) acts on it
and is hard-bounded by max_iterations regardless of what the judge says.
"""

from __future__ import annotations

from .config import ANTHROPIC_API_KEY, HAIKU_MODEL
from .sources.base import SourceError

_PROMPT = """You are the sufficiency gate for a daily tech-intelligence sweep.

Sufficiency means: did we SWEEP the sources properly? It does NOT mean we found
a lot. A quiet day with few items is complete and fine — do not manufacture work.
Only flag a source as a gap if it errored, returned suspiciously nothing, or is
clearly under-swept. When in doubt, answer SUFFICIENT: YES.

Coverage this run (source -> items fetched):
{coverage}
Errors: {errors}

Respond in EXACTLY four lines:
SUFFICIENT: YES or NO
QUIET_DAY: YES or NO
GAPS: comma-separated source names, or NONE
REASON: one short line
"""


def _parse(text: str, known: set[str]) -> dict:
    verdict = {"sufficient": True, "quiet_day": False, "gaps": [], "reason": ""}
    for line in text.splitlines():
        s = line.strip()
        upper = s.upper()
        if upper.startswith("SUFFICIENT:"):
            verdict["sufficient"] = "YES" in upper.split(":", 1)[1]
        elif upper.startswith("QUIET_DAY:"):
            verdict["quiet_day"] = "YES" in upper.split(":", 1)[1]
        elif upper.startswith("GAPS:"):
            raw = s.split(":", 1)[1].strip()
            if raw.upper() != "NONE":
                verdict["gaps"] = [g.strip() for g in raw.split(",") if g.strip() in known]
        elif upper.startswith("REASON:"):
            verdict["reason"] = s.split(":", 1)[1].strip()
    return verdict


def assess(coverage: dict[str, int], errors: list[SourceError], known: set[str]) -> dict:
    """Return a structured verdict. Errored sources are always gaps."""
    errored = sorted({e.source for e in errors})

    if not ANTHROPIC_API_KEY:
        return {
            "sufficient": not errored,
            "quiet_day": sum(coverage.values()) == 0 and not errored,
            "gaps": errored,
            "reason": "deterministic: retry errored sources" if errored else "all sources covered",
        }

    try:
        from anthropic import Anthropic

        msg = Anthropic().messages.create(
            model=HAIKU_MODEL,
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": _PROMPT.format(
                    coverage=coverage or "(nothing fetched)",
                    errors=", ".join(f"{e.source}: {e.message}" for e in errors) or "none",
                ),
            }],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        verdict = _parse(text, known)
    except Exception:
        # Fail toward termination — shipping a decent digest beats burning budget.
        verdict = {"sufficient": True, "quiet_day": False, "gaps": [], "reason": "judge unavailable"}

    # Errored sources are gaps regardless of what the model said.
    merged = sorted(set(verdict["gaps"]) | set(errored))
    verdict["gaps"] = merged
    if merged:
        verdict["sufficient"] = False
    return verdict
