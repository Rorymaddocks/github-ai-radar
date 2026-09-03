from __future__ import annotations

import math
from datetime import datetime, timezone

from .history import StarObservation
from .models import RankedRepository, Repository


LOW_UTILITY_MARKERS = {
    "awesome", "paper", "papers", "course", "courses", "interview", "roadmap",
    "tutorial", "tutorials", "learning", "resources", "survey",
}

CATEGORY_MARKERS = {
    "Trading / quant": ("trading", "quant", "algorithmic", "market-making", "market making", "hedge fund", "portfolio", "prediction market"),
    "Crypto / DeFi": ("crypto", "cryptocurrency", "defi", "web3", "blockchain", "ethereum", "solana", "onchain"),
    "Computer use": ("computer-use", "browser-use", "browser agent", "web agent"),
    "Coding agent": ("coding-agent", "coding agent", "coding-assistant", "ai-coding", "code-generation", "copilot"),
    "Voice agent": ("voice-agent", "voice agent", "realtime-agent", "speech-to-speech"),
    "Agent memory": ("agent-memory", "agent memory", "graph-rag", "graphrag", "long-term-memory"),
    "Evaluation / observability": ("agent-evals", "llm-evals", "llm-observability", "observability", "evaluation"),
    "MCP / integration": ("model-context-protocol", "mcp-server", "mcp server", "mcp-client"),
    "Agent framework": ("agent-framework", "ai-agents", "multi-agent", "agentic", "autonomous-agent"),
    "RAG / knowledge": ("rag", "retrieval-augmented-generation", "vector-database", "knowledge-base"),
    "Local model / inference": ("local-llm", "llm-inference", "inference-engine", "quantization"),
    "Robotics / embodied AI": ("embodied-ai", "world-model", "robotics-agent"),
    "Model tooling": ("llm", "inference", "fine-tuning", "machine-learning", "deep-learning"),
}


def classify(repo: Repository) -> str:
    haystack = " ".join((repo.full_name, repo.description, *repo.topics)).lower()
    for category, markers in CATEGORY_MARKERS.items():
        if any(marker in haystack for marker in markers):
            return category
    return "AI application"


def rank(
    repo: Repository,
    *,
    now: datetime | None = None,
    lanes: tuple[str, ...] = (),
    observation: StarObservation | None = None,
) -> RankedRepository:
    now = now or datetime.now(timezone.utc)
    age_days = max(1, (now - repo.created_at).days)
    updated_days = max(0, (now - repo.updated_at).days)
    velocity = repo.stars / age_days

    # Wide logarithmic scales keep large repositories from all saturating at 100.
    popularity = min(100.0, math.log10(repo.stars + 1) / 6 * 100)
    measured_velocity = observation.velocity if observation else velocity
    momentum = min(100.0, math.log10(measured_velocity + 1) / 3 * 100)
    pushed_days = max(0, (now - repo.pushed_at).days)
    freshness = max(0.0, 100.0 * math.exp(-pushed_days / 90))
    novelty = max(0.0, 100.0 * math.exp(-age_days / 540))
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
    fork_penalty = 35 if repo.is_fork else 0
    score = 0.25 * popularity + 0.35 * momentum + 0.20 * freshness + 0.15 * usability + 0.05 * novelty
    score = max(0.0, min(100.0, score - utility_penalty - archived_penalty - fork_penalty))

    if repo.stars >= 10_000:
        signal = "established"
    elif observation and observation.delta >= 10 and observation.velocity >= 2:
        signal = "breakout"
    elif age_days <= 180 and repo.stars <= 2_500:
        signal = "hidden gem"
    elif age_days <= 730 and (velocity >= 0.5 or pushed_days <= 14):
        signal = "rising"
    else:
        signal = "candidate"

    reasons: list[str] = []
    if repo.stars >= 10_000:
        reasons.append(f"established ({repo.stars:,} stars)")
    elif repo.stars >= 1_000:
        reasons.append(f"strong adoption ({repo.stars:,} stars)")
    if observation and observation.delta > 0:
        reasons.append(f"+{observation.delta:,} stars in {observation.days:.1f} days")
    elif velocity >= 20:
        reasons.append(f"very fast lifetime growth ({velocity:.1f} stars/day)")
    elif velocity >= 1:
        reasons.append(f"promising lifetime growth ({velocity:.1f} stars/day)")
    if pushed_days <= 14:
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
        signal=signal,
        discovery_lanes=lanes,
        recent_star_velocity=round(observation.velocity, 2) if observation else None,
        star_delta=observation.delta if observation else None,
        observation_days=round(observation.days, 2) if observation else None,
    )


def rank_all(
    repositories: list[Repository],
    *,
    now: datetime | None = None,
    lanes: dict[str, set[str]] | None = None,
    observations: dict[str, StarObservation] | None = None,
) -> list[RankedRepository]:
    lanes = lanes or {}
    observations = observations or {}
    items = (
        rank(
            repo,
            now=now,
            lanes=tuple(sorted(lanes.get(repo.full_name.lower(), set()))),
            observation=observations.get(repo.full_name.lower()),
        )
        for repo in repositories
    )
    return sorted(items, key=lambda item: item.score, reverse=True)
