"""GitHub releases adapter — new releases from a curated watchlist.

Reads the latest releases for each repo in `config/watchlist.yaml`. Uses
`GITHUB_TOKEN` when present (5,000 req/hr vs 60 unauth); the auto token in CI is
enough for a small watchlist. Star/org credibility signals need extra calls and
are added in Phase 1.5.
"""

from __future__ import annotations

import os

import httpx

from ..models import Finding
from .base import FetchResult, SourceError

RELEASES = "https://api.github.com/repos/{repo}/releases"
REPO = "https://api.github.com/repos/{repo}"


def parse(repo: str, releases: list[dict], meta: dict | None = None) -> list[Finding]:
    meta = meta or {}
    findings: list[Finding] = []
    for rel in releases:
        if rel.get("draft"):
            continue
        tag = rel.get("tag_name") or ""
        name = rel.get("name") or tag
        findings.append(
            Finding(
                source="github",
                external_id=f"{repo}@{tag}",
                url=rel.get("html_url", ""),
                title=f"{repo} {name}".strip(),
                published_at=rel.get("published_at", ""),
                author=(rel.get("author") or {}).get("login"),
                summary=(rel.get("body") or "")[:500] or None,
                credibility_signals={"prerelease": rel.get("prerelease", False), **meta},
                raw={"repo": repo, "tag": tag},
            )
        )
    return findings


class GitHubAdapter:
    name = "github"

    def __init__(self, repos: list[str]):
        self.repos = repos

    def fetch(self, cap: int) -> FetchResult:
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        findings: list[Finding] = []
        errors: list[SourceError] = []
        for repo in self.repos:
            try:
                meta = self._repo_meta(repo, headers)
                resp = httpx.get(
                    RELEASES.format(repo=repo),
                    headers=headers,
                    params={"per_page": 3},
                    timeout=20.0,
                )
                resp.raise_for_status()
                findings.extend(parse(repo, resp.json(), meta))
            except Exception as exc:  # fault isolation, per repo
                errors.append(SourceError(self.name, f"{repo}: {exc}"))
        return FetchResult(findings=findings[:cap], errors=errors)

    @staticmethod
    def _repo_meta(repo: str, headers: dict) -> dict:
        """Stars + owner type/login — raw credibility signals (one call/repo)."""
        try:
            resp = httpx.get(REPO.format(repo=repo), headers=headers, timeout=15.0)
            resp.raise_for_status()
            d = resp.json()
            owner = d.get("owner") or {}
            return {
                "stars": d.get("stargazers_count"),
                "owner_type": owner.get("type"),
                "owner_login": owner.get("login"),
            }
        except Exception:
            return {}
