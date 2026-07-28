"""Behavior model — a materialized view over the event log (Phase 2.3).

Rebuilt by folding events: per-source counts, and per-topic {shown, liked,
disliked, weight}. The weight is a deterministic function of feedback, so every
value is explainable and reproducible (fold events up to any date for
time-travel). Feedback shapes taste here — never the constitution.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import REPO_ROOT
from .seen_keys import normalize_url

BM_PATH = REPO_ROOT / "state" / "behavior_model.json"

_DEFAULT = {"runs": 0, "by_source": {}, "topics": {}, "updated": None, "last_run_id": None}

NEUTRAL_WEIGHT = 0.5


def _path(path: Path | None) -> Path:
    return path or BM_PATH


def _weight(liked: int, disliked: int) -> float:
    """Deterministic, explainable: 0.5 neutral, each like +0.08, each dislike
    -0.12, clamped to [0, 1]."""
    return round(max(0.0, min(1.0, NEUTRAL_WEIGHT + 0.08 * liked - 0.12 * disliked)), 4)


def load(path: Path | None = None) -> dict:
    p = _path(path)
    if not p.exists():
        return dict(_DEFAULT)
    return {**_DEFAULT, **json.loads(p.read_text(encoding="utf-8") or "{}")}


def save(model: dict, path: Path | None = None) -> None:
    p = _path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rebuild(events_list: list[dict], path: Path | None = None) -> dict:
    by_source: dict[str, int] = {}
    url_topics: dict[str, list[str]] = {}
    latest_feedback: dict[str, str] = {}
    runs = 0
    last_run = None

    for e in events_list:
        kind = e.get("type")
        if kind == "run_completed":
            runs += 1
            last_run = e.get("run_id")
        elif kind == "item_shown":
            src = e.get("source")
            by_source[src] = by_source.get(src, 0) + 1
            url_topics[normalize_url(e.get("url", ""))] = e.get("topics", [])
        elif kind == "feedback":
            latest_feedback[normalize_url(e.get("url", ""))] = e.get("signal")

    topics: dict[str, dict] = {}
    for url, tlist in url_topics.items():
        fb = latest_feedback.get(url)
        for topic in tlist:
            d = topics.setdefault(topic, {"shown": 0, "liked": 0, "disliked": 0})
            d["shown"] += 1
            if fb == "up":
                d["liked"] += 1
            elif fb == "down":
                d["disliked"] += 1
    for d in topics.values():
        d["weight"] = _weight(d["liked"], d["disliked"])

    model = {
        "runs": runs,
        "by_source": by_source,
        "topics": topics,
        "updated": last_run,
        "last_run_id": last_run,
    }
    save(model, path)
    return model


def topic_weights(path: Path | None = None) -> dict[str, float]:
    return {t: d.get("weight", NEUTRAL_WEIGHT) for t, d in load(path).get("topics", {}).items()}
