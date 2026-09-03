from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import Repository


@dataclass(frozen=True)
class StarObservation:
    delta: int
    days: float

    @property
    def velocity(self) -> float:
        return max(0.0, self.delta / self.days)


class SnapshotStore:
    def __init__(self, path: Path, *, max_snapshots: int = 60):
        self.path = path
        self.max_snapshots = max_snapshots

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return payload.get("snapshots", []) if payload.get("version") == 1 else []
        except (json.JSONDecodeError, OSError, AttributeError):
            return []

    def observations(self, repositories: list[Repository], now: datetime) -> dict[str, StarObservation]:
        snapshots = self.load()
        cutoff = now - timedelta(hours=6)
        eligible = []
        for snapshot in snapshots:
            try:
                captured = datetime.fromisoformat(snapshot["captured_at"])
                if captured <= cutoff:
                    eligible.append((captured, snapshot.get("repositories", {})))
            except (KeyError, TypeError, ValueError):
                continue
        if not eligible:
            return {}
        captured, stars = max(eligible, key=lambda item: item[0])
        days = max((now - captured).total_seconds() / 86400, 0.01)
        return {
            repo.full_name.lower(): StarObservation(repo.stars - int(stars[repo.full_name.lower()]), days)
            for repo in repositories
            if repo.full_name.lower() in stars
        }

    def record(self, repositories: list[Repository], now: datetime) -> None:
        snapshots = self.load()
        snapshots.append({
            "captured_at": now.astimezone(timezone.utc).isoformat(),
            "repositories": {repo.full_name.lower(): repo.stars for repo in repositories},
        })
        payload = {"version": 1, "snapshots": snapshots[-self.max_snapshots:]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
