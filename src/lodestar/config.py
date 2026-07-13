"""Configuration, repo-relative paths, and versioned YAML source config.

The constitution is loaded from the repo root and (in later phases) prepended
verbatim to every LLM context. Source configuration lives in `config/*.yaml`
so changes are visible in git and need no code change.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

# src/lodestar/config.py -> parents[2] is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"

# Model IDs — verified at build against the current Anthropic model line.
# Haiku-class for high-volume per-item work; Sonnet-class for the single overview.
HAIKU_MODEL = os.environ.get("LODESTAR_HAIKU_MODEL", "claude-haiku-4-5-20251001")
SONNET_MODEL = os.environ.get("LODESTAR_SONNET_MODEL", "claude-sonnet-5")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def load_constitution() -> str:
    return (REPO_ROOT / "constitution.md").read_text(encoding="utf-8")


def _load_yaml(name: str, default: dict) -> dict:
    path = CONFIG_DIR / name
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def arxiv_config() -> dict:
    return _load_yaml("arxiv.yaml", {"categories": ["cs.AI", "cs.CL", "cs.LG"], "cap": 15})


def github_watchlist() -> list[str]:
    return _load_yaml("watchlist.yaml", {"repos": []}).get("repos", [])


def exa_config() -> dict:
    return _load_yaml("domains.yaml", {"query": "", "domains": []})


def prefilter_config() -> dict:
    return _load_yaml(
        "prefilter.yaml", {"keywords": [], "filtered_sources": [], "caps": {}}
    )


def trusted_sources() -> dict:
    return _load_yaml("trusted_sources.yaml", {"orgs": [], "domains": [], "authors": []})
