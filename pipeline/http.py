"""Small HTTP helper: retries, GitHub rate-limit handling, Link-header pagination."""
from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any, Iterator

import requests

log = logging.getLogger("wiretap.http")

API = "https://api.github.com"
MAX_WAIT_SECONDS = 15 * 60


def github_token() -> str | None:
    """GITHUB_TOKEN in Actions; `gh auth token` locally; otherwise unauthenticated (60 req/h)."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() or None


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
             "User-Agent": "noir-wiretap"}
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.authenticated = bool(token)

    def _sleep_for_limit(self, resp: requests.Response) -> bool:
        """Return True if we waited and the caller should retry."""
        retry_after = resp.headers.get("Retry-After")
        remaining = resp.headers.get("X-RateLimit-Remaining")
        reset = resp.headers.get("X-RateLimit-Reset")
        if retry_after:
            wait = int(retry_after) + 1
        elif remaining == "0" and reset:
            wait = max(int(reset) - int(time.time()), 0) + 1
        else:
            return False
        if wait > MAX_WAIT_SECONDS:
            raise RuntimeError(
                f"GitHub rate limit resets in {wait}s (> {MAX_WAIT_SECONDS}s). "
                "Set GITHUB_TOKEN or log in with `gh auth login` and re-run."
            )
        log.warning("rate limited, sleeping %ss", wait)
        time.sleep(wait)
        return True

    def get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        for attempt in range(6):
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code in (403, 429) and self._sleep_for_limit(resp):
                continue
            if resp.status_code >= 500:
                time.sleep(2**attempt)
                continue
            return resp
        resp.raise_for_status()
        return resp

    def pages(self, path: str, params: dict[str, Any] | None = None,
              items_key: str | None = None, max_pages: int = 50) -> Iterator[list[dict]]:
        url: str | None = path if path.startswith("http") else f"{API}{path}"
        params = {"per_page": 100, **(params or {})}
        for _ in range(max_pages):
            if url is None:
                return
            resp = self.get(url, params)
            if resp.status_code == 409:  # empty repository
                return
            resp.raise_for_status()
            body = resp.json()
            yield body[items_key] if items_key else body
            url = resp.links.get("next", {}).get("url")
            params = None  # the next URL already carries the query
