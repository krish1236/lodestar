"""Render the sectioned digest to Markdown and write it to disk.

Layout (Topic 7): an optional overview, a cross-source Highlights section, then
per-source sections (Papers / Releases / Discussion). Each item shows its
credibility signals and the one-line "why this matters."

Writes:
  - digests/YYYY-MM-DD.md  — the permanent, dated archive (raw episodic store)
  - latest.md              — a stable pointer to the newest digest
"""

from __future__ import annotations

from datetime import datetime, timezone

from .config import REPO_ROOT
from .models import Finding
from .sources.base import SourceError


def _item_line(f: Finding) -> str:
    meta: list[str] = []
    if f.author:
        meta.append(f"@{f.author}")
    if (pts := f.credibility_signals.get("points")) is not None:
        meta.append(f"{pts} pts")
    if (stars := f.credibility_signals.get("stars")) is not None:
        meta.append(f"★{stars}")
    if (karma := f.credibility_signals.get("karma")) is not None:
        meta.append(f"{karma} karma")
    if f.credibility_signals.get("trusted"):
        meta.append("trusted")
    suffix = f" · {' · '.join(meta)}" if meta else ""
    lines = [f"- [{f.title}]({f.url}){suffix}"]
    if f.why:
        lines.append(f"  - {f.why}")
    return "\n".join(lines)


def render(
    run_date: str,
    overview: str | None,
    highlights: list[Finding],
    sections: dict[str, list[Finding]],
    coverage: dict[str, int],
    errors: list[SourceError],
) -> str:
    out = [f"# Daily Digest — {run_date}", ""]
    if overview:
        out += [f"> {overview}", ""]

    total = sum(len(v) for v in sections.values())
    if not total:
        out.append("_Quiet day — nothing on-mission surfaced._")
        out.append("")

    if highlights:
        out += ["## Highlights", ""] + [_item_line(f) for f in highlights] + [""]
    for section, items in sections.items():
        out += [f"## {section}", ""] + [_item_line(f) for f in items] + [""]

    out.append("---")
    # Coverage line: distinguishes a genuinely quiet day from a broken one.
    if coverage:
        cov = " · ".join(f"{s} {n}" for s, n in sorted(coverage.items()))
        out.append(f"_Coverage: {cov}_")
    for e in errors:
        out.append(f"> ⚠️ source `{e.source}` unavailable: {e.message}")

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out.append(f"_Generated {stamp} · Lodestar_")
    return "\n".join(out) + "\n"


def write_digest(markdown: str, run_date: str) -> None:
    digests_dir = REPO_ROOT / "digests"
    digests_dir.mkdir(exist_ok=True)
    (digests_dir / f"{run_date}.md").write_text(markdown, encoding="utf-8")
    (REPO_ROOT / "latest.md").write_text(markdown, encoding="utf-8")
