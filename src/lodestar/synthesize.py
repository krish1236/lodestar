"""Minimal synthesizer for Phase 0.

Its only job here is to attach a one-line "why this matters for you" to each
finding, judged against the constitution. This exists mainly to prove the
Anthropic key + model path end to end. If no API key is present, it degrades
gracefully (leaves `why` unset) so the pipeline is testable offline.

Real ranking, sectioning, and the single Sonnet synthesis call arrive in
Phase 1.6.
"""

from __future__ import annotations

from .config import ANTHROPIC_API_KEY, HAIKU_MODEL
from .models import Finding

_PROMPT = """You are curating a daily tech-intelligence digest for a senior \
engineer who builds AI agents. Here is their mission and interests:

<constitution>
{constitution}
</constitution>

For the item below, write ONE short sentence (max 20 words) on why it matters \
to this engineer. If it is off-mission or low-signal, reply with exactly SKIP.

Title: {title}
URL: {url}
"""


def add_why(findings: list[Finding], constitution: str) -> list[Finding]:
    if not ANTHROPIC_API_KEY:
        return findings  # offline / no-key mode: skip the one-liners

    from anthropic import Anthropic

    client = Anthropic()
    for f in findings:
        try:
            msg = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=60,
                messages=[
                    {
                        "role": "user",
                        "content": _PROMPT.format(
                            constitution=constitution, title=f.title, url=f.url
                        ),
                    }
                ],
            )
            text = "".join(
                block.text for block in msg.content if getattr(block, "type", None) == "text"
            ).strip()
            f.why = None if text.upper().startswith("SKIP") else text
        except Exception:
            # A per-item failure must not sink the run — leave why unset.
            f.why = None
    return findings
