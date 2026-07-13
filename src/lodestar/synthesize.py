"""Synthesis LLM calls: per-item relevance (Haiku) and a digest overview (Sonnet).

Model tiering: the high-volume per-item scoring uses the fast model; the single
overview call uses the stronger model. Both degrade gracefully without a key
(relevance defaults to neutral, overview is skipped) so the pipeline runs offline.
"""

from __future__ import annotations

from .config import ANTHROPIC_API_KEY, HAIKU_MODEL, SONNET_MODEL
from .models import Finding

_SCORE_PROMPT = """You curate a daily tech-intelligence digest for a senior \
engineer who builds AI agents. Their mission and interests:

<constitution>
{constitution}
</constitution>

Score this item's relevance and signal for them. Respond in EXACTLY two lines:
SCORE: <0-5, where 0 = off-mission/noise, 5 = must-read>
WHY: <one short line on why it matters, or NONE if off-mission>

Title: {title}
Summary: {summary}
"""

_OVERVIEW_PROMPT = """In one sentence (max 25 words), state the theme connecting \
today's top AI/agent items for a senior engineer. Be specific, no hype.

{titles}
"""


def _text(msg) -> str:
    return "".join(
        b.text for b in msg.content if getattr(b, "type", None) == "text"
    ).strip()


def _parse_score(text: str) -> tuple[float, str | None]:
    score, why = 0.5, None
    for line in text.splitlines():
        s = line.strip()
        if s.upper().startswith("SCORE:"):
            try:
                score = max(0.0, min(1.0, float(s.split(":", 1)[1].strip()) / 5.0))
            except ValueError:
                pass
        elif s.upper().startswith("WHY:"):
            w = s.split(":", 1)[1].strip()
            why = None if w.upper() == "NONE" else w
    return score, why


def score_relevance(findings: list[Finding], constitution: str) -> list[Finding]:
    if not ANTHROPIC_API_KEY:
        for f in findings:
            f.relevance = 0.5  # neutral: everything passes the gate offline
        return findings

    from anthropic import Anthropic

    client = Anthropic()
    for f in findings:
        try:
            msg = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=80,
                messages=[
                    {
                        "role": "user",
                        "content": _SCORE_PROMPT.format(
                            constitution=constitution,
                            title=f.title,
                            summary=(f.summary or "")[:400],
                        ),
                    }
                ],
            )
            f.relevance, f.why = _parse_score(_text(msg))
        except Exception:
            f.relevance = 0.5  # non-fatal — treat as neutral
    return findings


def overview(highlights: list[Finding], constitution: str) -> str | None:
    if not ANTHROPIC_API_KEY or not highlights:
        return None
    titles = "\n".join(f"- {f.title}" for f in highlights)
    try:
        from anthropic import Anthropic

        client = Anthropic()
        msg = client.messages.create(
            model=SONNET_MODEL,
            max_tokens=80,
            messages=[{"role": "user", "content": _OVERVIEW_PROMPT.format(titles=titles)}],
        )
        return _text(msg) or None
    except Exception:
        return None
