"""Render findings to Markdown and write them to disk.

Phase 0 writes two files:
  - digests/YYYY-MM-DD.md  — the permanent, dated archive (raw episodic store)
  - latest.md              — a stable pointer to the newest digest

The architecture write-up stays in README.md.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .config import REPO_ROOT
from .models import Finding
from .sources.base import SourceError


def render(findings: list[Finding], run_date: str, errors: list[SourceError]) -> str:
    lines = [f"# Daily Digest — {run_date}", ""]

    if not findings:
        lines.append("_Quiet day — nothing surfaced._")
    for f in findings:
        meta = []
        if f.author:
            meta.append(f"@{f.author}")
        points = f.credibility_signals.get("points")
        if points is not None:
            meta.append(f"{points} pts")
        suffix = f" · {' · '.join(meta)}" if meta else ""
        lines.append(f"- [{f.title}]({f.url}){suffix}")
        if f.why:
            lines.append(f"  - {f.why}")

    lines.append("")
    if errors:
        lines.append("---")
        for e in errors:
            lines.append(f"> ⚠️ source `{e.source}` unavailable: {e.message}")
        lines.append("")

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines.append(f"_Generated {stamp} · Lodestar_")
    return "\n".join(lines) + "\n"


def write_digest(markdown: str, run_date: str) -> None:
    digests_dir = REPO_ROOT / "digests"
    digests_dir.mkdir(exist_ok=True)
    (digests_dir / f"{run_date}.md").write_text(markdown, encoding="utf-8")
    (REPO_ROOT / "latest.md").write_text(markdown, encoding="utf-8")
