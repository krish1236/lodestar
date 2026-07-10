"""Configuration and repo-relative paths.

The constitution is loaded from the repo root and (in later phases) prepended
verbatim to every LLM context. For now it is loaded so the synthesizer can
judge relevance against it.
"""

from __future__ import annotations

import os
from pathlib import Path

# src/lodestar/config.py -> parents[2] is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Model IDs — verified at build against the current Anthropic model line.
# Haiku-class handles the high-volume per-item work; a stronger model is used
# for synthesis/judge in later phases.
HAIKU_MODEL = os.environ.get("LODESTAR_HAIKU_MODEL", "claude-haiku-4-5-20251001")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def load_constitution() -> str:
    return (REPO_ROOT / "constitution.md").read_text(encoding="utf-8")
