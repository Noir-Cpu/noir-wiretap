"""GitHub activity for the NOIR repos: repos, commits, workflow runs, pull requests, releases.

Deliberately not extracted: commit author names and e-mail addresses. Only public logins.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Iterator

import dlt

from .http import GitHubClient, github_token

OWNER = os.environ.get("WIRETAP_GITHUB_OWNER", "Noir-Cpu")
REPO_PREFIX = os.environ.get("WIRETAP_REPO_PREFIX", "noir-")
# Workflow runs and PRs change after creation (in progress -> completed), so re-read a window.
LOOKBACK = timedelta(days=3)
FIRST_LOAD_SINCE = "2020-01-01T00:00:00Z"


def _login(obj: dict | None) -> str | None:
    return (obj or {}).get("login")


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lookback_from(cursor: str | None) -> str:
    if not cursor:
        return FIRST_LOAD_SINCE
    parsed = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
    return _iso(parsed - LOOKBACK)


def _client() -> GitHubClient:
    return GitHubClient(github_token())


def list_repos(client: GitHubClient) -> list[dict]:
    repos: list[dict] = []
    for page in client.pages(f"/users/{OWNER}/repos", {"type": "owner"}):
        repos.extend(r for r in page if r["name"].startswith(REPO_PREFIX))
    return sorted(repos, key=lambda r: r["name"])


@dlt.source(name="github")
def github_source(repo_names: list[str] | None = None):
    client = _client()
    all_repos = list_repos(client)
    repos = [r for r in all_repos if repo_names is None or r["name"] in repo_names]

    @dlt.resource(name="repos", write_disposition="replace", primary_key="id")
    def repos_resource() -> Iterator[dict]:
        for r in repos:
            yield {
                "id": r["id"], "name": r["name"], "full_name": r["full_name"],
                "description": r.get("description"), "language": r.get("language"),
                "default_branch": r["default_branch"], "archived": r["archived"],
                "fork": r["fork"], "visibility": r.get("visibility", "public"),
                "topics": ",".join(sorted(r.get("topics") or [])),
                "stargazers_count": r["stargazers_count"], "forks_count": r["forks_count"],
                "open_issues_count": r["open_issues_count"], "created_at": r["created_at"],
                "pushed_at": r["pushed_at"], "updated_at": r["updated_at"],
            }

    @dlt.resource(name="commits", write_disposition="merge", primary_key=("repo", "sha"))
    def commits_resource() -> Iterator[dict]:
        state = dlt.current.resource_state().setdefault("cursor", {})
        for r in repos:
            newest = state.get(r["name"])
            params = {"since": _lookback_from(newest)}
            for page in client.pages(f"/repos/{OWNER}/{r['name']}/commits", params):
                for c in page:
                    committed = c["commit"]["committer"]["date"]
                    newest = max(newest or committed, committed)
                    yield {
                        "repo": r["name"], "sha": c["sha"],
                        "committed_at": committed, "authored_at": c["commit"]["author"]["date"],
                        "author_login": _login(c.get("author")),
                        "committer_login": _login(c.get("committer")),
                        "message_headline": c["commit"]["message"].splitlines()[0][:200],
                    }
            if newest:
                state[r["name"]] = newest

    @dlt.resource(name="workflow_runs", write_disposition="merge", primary_key=("repo", "id"))
    def runs_resource() -> Iterator[dict]:
        state = dlt.current.resource_state().setdefault("cursor", {})
        for r in repos:
            newest = state.get(r["name"])
            params = {"created": f">={_lookback_from(newest)}"}
            for page in client.pages(
                f"/repos/{OWNER}/{r['name']}/actions/runs", params, items_key="workflow_runs"
            ):
                for w in page:
                    newest = max(newest or w["created_at"], w["created_at"])
                    yield {
                        "repo": r["name"], "id": w["id"], "workflow_id": w["workflow_id"],
                        "name": w["name"], "event": w["event"], "head_branch": w["head_branch"],
                        "status": w["status"], "conclusion": w["conclusion"],
                        "run_number": w["run_number"], "run_attempt": w["run_attempt"],
                        "created_at": w["created_at"], "run_started_at": w["run_started_at"],
                        "updated_at": w["updated_at"], "actor_login": _login(w.get("actor")),
                    }
            if newest:
                state[r["name"]] = newest

    @dlt.resource(name="pull_requests", write_disposition="merge", primary_key=("repo", "id"))
    def prs_resource() -> Iterator[dict]:
        state = dlt.current.resource_state().setdefault("cursor", {})
        for r in repos:
            newest = state.get(r["name"])
            floor = _lookback_from(newest)
            params = {"state": "all", "sort": "updated", "direction": "desc"}
            done = False
            for page in client.pages(f"/repos/{OWNER}/{r['name']}/pulls", params):
                for p in page:
                    if p["updated_at"] < floor:
                        done = True
                        break
                    newest = max(newest or p["updated_at"], p["updated_at"])
                    yield {
                        "repo": r["name"], "id": p["id"], "number": p["number"],
                        "state": p["state"], "draft": p.get("draft", False),
                        "created_at": p["created_at"], "updated_at": p["updated_at"],
                        "closed_at": p["closed_at"], "merged_at": p["merged_at"],
                        "author_login": _login(p.get("user")), "base_ref": p["base"]["ref"],
                    }
                if done:
                    break
            if newest:
                state[r["name"]] = newest

    @dlt.resource(name="releases", write_disposition="merge", primary_key=("repo", "id"))
    def releases_resource() -> Iterator[dict]:
        for r in repos:
            for page in client.pages(f"/repos/{OWNER}/{r['name']}/releases"):
                for rel in page:
                    yield {
                        "repo": r["name"], "id": rel["id"], "tag_name": rel["tag_name"],
                        "name": rel["name"], "draft": rel["draft"],
                        "prerelease": rel["prerelease"], "created_at": rel["created_at"],
                        "published_at": rel["published_at"],
                    }

    return repos_resource, commits_resource, runs_resource, prs_resource, releases_resource
