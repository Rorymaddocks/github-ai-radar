from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


def parse_github_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class Repository:
    full_name: str
    html_url: str
    description: str
    stars: int
    forks: int
    open_issues: int
    language: str
    topics: tuple[str, ...]
    license: str
    created_at: datetime
    updated_at: datetime
    archived: bool
    homepage: str
    owner_login: str
    owner_url: str
    owner_type: str
    pushed_at: datetime
    is_fork: bool

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "Repository":
        license_data = item.get("license") or {}
        owner = item.get("owner") or {}
        return cls(
            full_name=item["full_name"],
            html_url=item["html_url"],
            description=(item.get("description") or "").strip(),
            stars=int(item.get("stargazers_count", 0)),
            forks=int(item.get("forks_count", 0)),
            open_issues=int(item.get("open_issues_count", 0)),
            language=item.get("language") or "Unknown",
            topics=tuple(item.get("topics") or ()),
            license=license_data.get("spdx_id") or "None detected",
            created_at=parse_github_date(item["created_at"]),
            updated_at=parse_github_date(item["updated_at"]),
            archived=bool(item.get("archived", False)),
            homepage=item.get("homepage") or "",
            owner_login=owner.get("login") or item["full_name"].split("/", 1)[0],
            owner_url=owner.get("html_url") or "",
            owner_type=owner.get("type") or "Unknown",
            pushed_at=parse_github_date(item.get("pushed_at") or item["updated_at"]),
            is_fork=bool(item.get("fork", False)),
        )


@dataclass(frozen=True)
class RankedRepository:
    repository: Repository
    score: float
    category: str
    star_velocity: float
    age_days: int
    updated_days_ago: int
    reasons: tuple[str, ...]
    signal: str = "candidate"
    discovery_lanes: tuple[str, ...] = ()
    recent_star_velocity: float | None = None
    star_delta: int | None = None
    observation_days: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["repository"]["created_at"] = self.repository.created_at.isoformat()
        result["repository"]["updated_at"] = self.repository.updated_at.isoformat()
        return result


@dataclass(frozen=True)
class Creator:
    login: str
    html_url: str
    account_type: str
    score: float
    discovered_repositories: int
    total_stars: int
    best_repository: str
    best_repository_score: float
    breakout_projects: int
    reasons: tuple[str, ...]
    followers: int | None = None
    bio: str = ""
    profile_created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreatorProfile:
    login: str
    followers: int
    public_repos: int
    bio: str
    created_at: datetime

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "CreatorProfile":
        return cls(
            login=item["login"],
            followers=int(item.get("followers", 0)),
            public_repos=int(item.get("public_repos", 0)),
            bio=(item.get("bio") or "").strip(),
            created_at=parse_github_date(item["created_at"]),
        )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
