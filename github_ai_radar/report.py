from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Creator, RankedRepository


EMERGING_SIGNALS = {"breakout", "hidden gem", "rising"}


def diverse(items: list[RankedRepository], limit: int) -> list[RankedRepository]:
    """Prevent one owner or category from monopolizing the discovery list."""
    selected: list[RankedRepository] = []
    owner_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    category_cap = max(2, (limit + 2) // 3)
    for item in items:
        owner = item.repository.owner_login
        if owner_counts.get(owner, 0) >= 2 or category_counts.get(item.category, 0) >= category_cap:
            continue
        selected.append(item)
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        category_counts[item.category] = category_counts.get(item.category, 0) + 1
        if len(selected) == limit:
            break
    if len(selected) < limit:
        selected_ids = {item.repository.full_name for item in selected}
        selected.extend(item for item in items if item.repository.full_name not in selected_ids)
    return selected[:limit]


def select_sections(items: list[RankedRepository], limit: int, mode: str) -> list[tuple[str, list[RankedRepository]]]:
    breakouts = diverse([item for item in items if item.signal in {"breakout", "rising"}], limit)
    hidden_gems = diverse([item for item in items if item.signal == "hidden gem"], limit)
    established = diverse([item for item in items if item.signal == "established"], limit)
    if mode == "emerging":
        return [("Breakouts and fast risers", breakouts), ("Hidden gems", hidden_gems)]
    if mode == "established":
        return [("Established projects", established)]
    return [("Breakouts and fast risers", breakouts), ("Hidden gems", hidden_gems), ("Established projects", established)]


def _velocity(item: RankedRepository) -> str:
    if item.recent_star_velocity is not None:
        return f"{item.recent_star_velocity:.2f}/day observed"
    return f"{item.star_velocity:.2f}/day lifetime"


def render_terminal(items: list[RankedRepository], creators: list[Creator], limit: int, mode: str = "all") -> str:
    lines: list[str] = []
    for heading, rows in select_sections(items, limit, mode):
        lines.extend([heading, "=" * len(heading)])
        if not rows:
            lines.append("No matching repositories found.")
        for index, item in enumerate(rows, 1):
            repo = item.repository
            reasons = "; ".join(item.reasons) or "matched a frontier search"
            lines.extend([
                f"{index:>2}. {repo.full_name}  [{item.score:.1f} · {item.signal}]",
                f"    {repo.stars:,} stars · {_velocity(item)} · {item.category} · {repo.language}",
                f"    {reasons}",
                f"    {repo.html_url}",
            ])
        lines.append("")
    if mode != "established" and creators:
        lines.extend(["Emerging creators", "================="])
        emerging_creators = [creator for creator in creators if creator.breakout_projects]
        for index, creator in enumerate(emerging_creators[: min(10, limit)], 1):
            audience = f" · {creator.followers:,} followers" if creator.followers is not None else ""
            lines.append(
                f"{index:>2}. {creator.login} [{creator.score:.1f}] · {creator.discovered_repositories} projects · "
                f"best: {creator.best_repository}{audience} · {creator.html_url}"
            )
    return "\n".join(lines).rstrip()


def write_json(items: list[RankedRepository], creators: list[Creator], path: Path, *, generated_at: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": generated_at.isoformat(),
        "repositories": [item.to_dict() for item in items],
        "creators": [creator.to_dict() for creator in creators],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(
    items: list[RankedRepository], creators: list[Creator], path: Path, *,
    generated_at: datetime, limit: int, mode: str = "all",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# GitHub AI Radar", "", f"Generated {generated_at.isoformat(timespec='seconds')}", ""]
    for heading, rows in select_sections(items, limit, mode):
        lines.extend([
            f"## {heading}", "",
            "| # | Repository | Signal | Score | Stars | Velocity | Category | Why it surfaced |",
            "|---:|---|---|---:|---:|---:|---|---|",
        ])
        for index, item in enumerate(rows, 1):
            repo = item.repository
            description = repo.description.replace("|", "\\|")
            reasons = "; ".join(item.reasons).replace("|", "\\|")
            lines.append(
                f"| {index} | [{repo.full_name}]({repo.html_url})<br>{description} | {item.signal} | {item.score:.1f} | "
                f"{repo.stars:,} | {_velocity(item)} | {item.category} | {reasons} |"
            )
        lines.append("")
    if mode != "established" and creators:
        lines.extend([
            "## Emerging creators", "",
            "| # | Creator | Score | Followers | Relevant projects | Emerging signals | Best project |",
            "|---:|---|---:|---:|---:|---:|---|",
        ])
        emerging_creators = [creator for creator in creators if creator.breakout_projects]
        for index, creator in enumerate(emerging_creators[: min(10, limit)], 1):
            lines.append(
                f"| {index} | [{creator.login}]({creator.html_url}) | {creator.score:.1f} | "
                f"{creator.followers if creator.followers is not None else 'unknown'} | {creator.discovered_repositories} | "
                f"{creator.breakout_projects} | {creator.best_repository} |"
            )
        lines.append("")
    lines.extend([
        "> Observed velocity uses changes between local snapshots at least six hours apart. Until a baseline exists, "
        "the report clearly labels its age-adjusted lifetime estimate.", "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
