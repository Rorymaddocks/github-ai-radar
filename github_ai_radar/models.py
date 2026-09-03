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

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "Repository":
        license_data = item.get("license") or {}
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

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["repository"]["created_at"] = self.repository.created_at.isoformat()
        result["repository"]["updated_at"] = self.repository.updated_at.isoformat()
        return result


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

