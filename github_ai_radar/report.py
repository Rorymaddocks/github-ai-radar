from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import RankedRepository


def render_terminal(items: list[RankedRepository], limit: int) -> str:
    rows = items[:limit]
    if not rows:
        return "No matching repositories found."
    lines = []
    for index, item in enumerate(rows, 1):
        repo = item.repository
        reasons = "; ".join(item.reasons) or "matched AI search"
        lines.extend([
            f"{index:>2}. {repo.full_name}  [{item.score:.1f}]",
            f"    {repo.stars:,} stars · {item.star_velocity:.2f}/day · {item.category} · {repo.language}",
            f"    {reasons}",
            f"    {repo.html_url}",
        ])
    return "\n".join(lines)


def write_json(items: list[RankedRepository], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([item.to_dict() for item in items], indent=2), encoding="utf-8")


def write_markdown(items: list[RankedRepository], path: Path, *, generated_at: datetime, limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GitHub AI Radar",
        "",
        f"Generated {generated_at.isoformat(timespec='seconds')}",
        "",
        "| # | Repository | Score | Stars | Stars/day | Category | License | Why it surfaced |",
        "|---:|---|---:|---:|---:|---|---|---|",
    ]
    for index, item in enumerate(items[:limit], 1):
        repo = item.repository
        description = repo.description.replace("|", "\\|")
        reasons = "; ".join(item.reasons).replace("|", "\\|")
        lines.append(
            f"| {index} | [{repo.full_name}]({repo.html_url})<br>{description} | {item.score:.1f} | "
            f"{repo.stars:,} | {item.star_velocity:.2f} | {item.category} | {repo.license} | {reasons} |"
        )
    lines.extend(["", "Scores blend adoption, lifetime star velocity, recent activity, and usability signals.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")

