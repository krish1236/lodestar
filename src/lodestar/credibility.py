"""Derived credibility annotation — deterministic, applied at collection.

Adapters attach *raw* signals (karma, stars, owner type, domain). This adds the
one derived signal that needs cross-source config: `trusted`, from the allowlist.
No weighting happens here — that's the ranking stage (Phase 1.6). `trusted` is a
boost input, never a filter.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from .config import trusted_sources
from .models import Finding


def _host(url: str) -> str:
    return urlsplit(url).netloc.lower().removeprefix("www.")


def mark_trusted(findings: list[Finding], allowlist: dict | None = None) -> list[Finding]:
    al = allowlist if allowlist is not None else trusted_sources()
    orgs = {o.lower() for o in al.get("orgs", [])}
    domains = {d.lower() for d in al.get("domains", [])}
    authors = {a.lower() for a in al.get("authors", [])}

    for f in findings:
        login = str(f.credibility_signals.get("owner_login", "")).lower()
        host = _host(f.url)
        trusted = (
            (login in orgs)
            or any(host == d or host.endswith("." + d) for d in domains)
            or (bool(f.author) and f.author.lower() in authors)
        )
        f.credibility_signals["trusted"] = trusted
    return findings
