from __future__ import annotations

import json
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import CreatorProfile, Repository


API_URL = "https://api.github.com/search/repositories"
USERS_URL = "https://api.github.com/users"


class GitHubError(RuntimeError):
    pass


@dataclass
class GitHubClient:
    token: str = ""
    cache_dir: Path = Path(".radar-cache")
    cache_ttl_seconds: int = 3600

    def search(self, query: str, *, per_page: int = 50, page: int = 1, sort: str = "stars") -> list[Repository]:
        if sort not in {"stars", "forks", "help-wanted-issues", "updated"}:
            raise ValueError(f"Unsupported repository sort: {sort}")
        params = urlencode({"q": query, "sort": sort, "order": "desc", "per_page": per_page, "page": page})
        url = f"{API_URL}?{params}"
        payload = self._get_json(url)
        return [Repository.from_api(item) for item in payload.get("items", [])]

    def creator_profile(self, login: str) -> CreatorProfile:
        return CreatorProfile.from_api(self._get_json(f"{USERS_URL}/{login}"))

    def _get_json(self, url: str) -> dict[str, Any]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists() and time.time() - cache_file.stat().st_mtime < self.cache_ttl_seconds:
            return json.loads(cache_file.read_text(encoding="utf-8"))

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-ai-radar/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in (403, 429):
                raise GitHubError("GitHub rate limit reached. Set GITHUB_TOKEN and try again.") from exc
            raise GitHubError(f"GitHub API returned HTTP {exc.code}: {detail[:300]}") from exc
        except URLError as exc:
            raise GitHubError(f"Could not reach GitHub: {exc.reason}") from exc

        cache_file.write_text(json.dumps(payload), encoding="utf-8")
        return payload
