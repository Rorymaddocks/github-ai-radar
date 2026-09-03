from __future__ import annotations

import math
from datetime import datetime, timezone

from .models import RankedRepository, Repository


LOW_UTILITY_MARKERS = {
    "awesome", "paper", "papers", "course", "courses", "interview", "roadmap",
    "tutorial", "tutorials", "learning", "resources", "survey",
}

CATEGORY_MARKERS = {
    "Agent framework": ("agent-framework", "agents", "multi-agent", "agentic", "autonomous-agent"),
    "Developer tool": ("copilot", "coding-assistant", "developer-tools", "ai-coding", "code-generation"),
    "RAG / knowledge": ("rag", "retrieval-augmented-generation", "vector-database", "knowledge-base"),
    "Model tooling": ("llm", "inference", "fine-tuning", "machine-learning", "deep-learning"),
}


def classify(repo: Repository) -> str:
    haystack = " ".join((repo.full_name, repo.description, *repo.topics)).lower()
    for category, markers in CATEGORY_MARKERS.items():
        if any(marker in haystack for marker in markers):
            return category
    return "AI application"


def rank(repo: Repository, *, now: datetime | None = None) -> RankedRepository:
    now = now or datetime.now(timezone.utc)
    age_days = max(1, (now - repo.created_at).days)
    updated_days = max(0, (now - repo.updated_at).days)
    velocity = repo.stars / age_days

    # Wide logarithmic scales keep large repositories from all saturating at 100.
    popularity = min(100.0, math.log10(repo.stars + 1) / 6 * 100)
    momentum = min(100.0, math.log10(velocity + 1) / 4 * 100)
    freshness = max(0.0, 100.0 * math.exp(-updated_days / 120))
    usability = 0.0
    usability += 30 if repo.license != "None detected" else 0
    usability += 20 if repo.description else 0
    usability += 15 if repo.language != "Unknown" else 0
    usability += 10 if repo.topics else 0
    usability += 10 if repo.homepage else 0
    usability += min(15, math.log10(repo.forks + 1) * 5)

    text_markers = set(" ".join((repo.full_name, repo.description, *repo.topics)).lower().replace("/", " ").replace("-", " ").split())
    utility_penalty = 22 if text_markers & LOW_UTILITY_MARKERS else 0
    archived_penalty = 60 if repo.archived else 0
    score = 0.34 * popularity + 0.31 * momentum + 0.20 * freshness + 0.15 * usability
    score = max(0.0, min(100.0, score - utility_penalty - archived_penalty))

    reasons: list[str] = []
    if repo.stars >= 10_000:
        reasons.append(f"established ({repo.stars:,} stars)")
    elif repo.stars >= 1_000:
        reasons.append(f"strong adoption ({repo.stars:,} stars)")
    if velocity >= 20:
        reasons.append(f"very fast growth ({velocity:.1f} stars/day lifetime)")
    elif velocity >= 3:
        reasons.append(f"growing ({velocity:.1f} stars/day lifetime)")
    if updated_days <= 14:
        reasons.append("recently active")
    if repo.license != "None detected":
        reasons.append(f"{repo.license} licensed")
    if utility_penalty:
        reasons.append("resource/list-like repository")

    return RankedRepository(
        repository=repo,
        score=round(score, 1),
        category=classify(repo),
        star_velocity=round(velocity, 2),
        age_days=age_days,
        updated_days_ago=updated_days,
        reasons=tuple(reasons),
    )


def rank_all(repositories: list[Repository], *, now: datetime | None = None) -> list[RankedRepository]:
    return sorted((rank(repo, now=now) for repo in repositories), key=lambda item: item.score, reverse=True)
