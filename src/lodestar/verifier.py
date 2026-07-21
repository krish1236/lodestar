"""Adversarial verifier (Phase 2.1) — per-item, concurrent, after dedup+prefilter.

Two jobs:
  1. Reachability (deterministic HEAD/GET) — drop dead links. Fails OPEN: only a
     definitive 404/410/451 or a DNS/connection failure drops an item, so a live
     page that merely blocks bots (403) or times out is kept.
  2. Substance gate (Haiku) — drop on-topic hype/marketing/clickbait that the
     relevance score might still rate moderately. Fails OPEN (keep) on any error.

Items are checked in parallel (network/LLM I/O bound), each in isolation.
Removed items are NOT surfaced but are still marked seen upstream, so we don't
re-verify them every day.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import httpx

from .config import ANTHROPIC_API_KEY, HAIKU_MODEL
from .models import Finding

_DEAD = {404, 410, 451}

_SUBSTANCE_PROMPT = """Is this a substantive, technical item worth a senior AI \
engineer's time, or is it marketing/hype/clickbait/low-signal?
Reply with one word: KEEP or DROP. If unsure, reply KEEP.

Title: {title}
Summary: {summary}
"""


def _reachable(url: str) -> bool:
    if not url:
        return False
    try:
        r = httpx.head(url, timeout=8.0, follow_redirects=True)
        if r.status_code in (403, 405):  # some servers reject HEAD — try GET
            r = httpx.get(url, timeout=8.0, follow_redirects=True)
        return r.status_code not in _DEAD
    except httpx.HTTPError:
        return True  # network hiccup — fail open, don't drop a maybe-live link


def _substantive(finding: Finding, client) -> bool:
    try:
        msg = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=5,
            messages=[
                {
                    "role": "user",
                    "content": _SUBSTANCE_PROMPT.format(
                        title=finding.title, summary=(finding.summary or "")[:400]
                    ),
                }
            ],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return not text.strip().upper().startswith("DROP")
    except Exception:
        return True  # fail open


def verify(findings: list[Finding]) -> list[Finding]:
    if not findings:
        return []

    with ThreadPoolExecutor(max_workers=8) as ex:
        reachable = list(ex.map(lambda f: _reachable(f.url), findings))
    survivors = [f for f, ok in zip(findings, reachable) if ok]

    if ANTHROPIC_API_KEY and survivors:
        try:
            from anthropic import Anthropic

            client = Anthropic()
        except Exception:
            return survivors  # can't run substance check — keep all (fail open)
        with ThreadPoolExecutor(max_workers=6) as ex:
            keep = list(ex.map(lambda f: _substantive(f, client), survivors))
        survivors = [f for f, ok in zip(survivors, keep) if ok]

    return survivors
