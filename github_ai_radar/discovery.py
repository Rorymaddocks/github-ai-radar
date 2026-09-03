from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class SearchSpec:
    lane: str
    query: str
    sort: str = "stars"


# Distinct vocabularies matter: early projects often have not adopted the most
# popular GitHub topics yet. Keep these focused enough to stay below GitHub's
# authenticated search-rate budget in a normal scan.
GENERAL_ESTABLISHED = (
    "topic:ai-agents",
    "topic:agent-framework",
    '"coding agent" in:name,description',
    "topic:rag",
    "topic:llmops",
)

GENERAL_FRONTIERS = (
    ("agentic", "agentic in:name,description"),
    ("multi-agent", '"multi agent" in:name,description'),
    ("coding-agents", '"coding agent" in:name,description'),
    ("computer-use", '"computer use" in:name,description'),
    ("mcp", '"model context protocol" in:name,description'),
    ("voice-agents", '"voice agent" in:name,description'),
    ("memory-rag", '"agent memory" in:name,description'),
    ("evals-observability", '"llm observability" in:name,description'),
    ("local-inference", '"local llm" in:name,description'),
    ("robotics-world-models", '"embodied ai" in:name,description'),
)

WEB3_ESTABLISHED = (
    'topic:defi',
    'topic:crypto-trading',
    'topic:algorithmic-trading',
    'topic:quantitative-finance',
    'topic:web3',
)

WEB3_FRONTIERS = (
    ("crypto-agents", 'crypto agent in:name,description'),
    ("trading-agents", 'trading agent in:name,description'),
    ("quant", 'quantitative trading in:name,description'),
    ("algorithmic-trading", 'algorithmic trading in:name,description'),
    ("defi", 'defi in:name,description'),
    ("onchain", 'onchain in:name,description'),
    ("market-making", 'market making in:name,description'),
    ("hedge-fund", 'hedge fund in:name,description'),
    ("portfolio", 'crypto portfolio in:name,description'),
    ("prediction-markets", 'prediction market in:name,description'),
)


def default_specs(now: datetime, *, focus: str = "web3", max_stars: int = 10_000) -> list[SearchSpec]:
    year_ago = (now - timedelta(days=365)).date().isoformat()
    ninety_days_ago = (now - timedelta(days=90)).date().isoformat()
    established = WEB3_ESTABLISHED if focus == "web3" else GENERAL_ESTABLISHED
    frontiers = WEB3_FRONTIERS if focus == "web3" else GENERAL_FRONTIERS
    ceiling = f"..{max_stars}" if max_stars else ""
    established_range = f"stars:100{ceiling}" if max_stars else "stars:>=100"
    rising_range = f"stars:15{ceiling}" if max_stars else "stars:>=15"
    specs = [SearchSpec("established", f"{query} {established_range} archived:false fork:false") for query in established]
    for frontier, query in frontiers:
        specs.append(SearchSpec(f"rising/{frontier}", f"{query} created:>={year_ago} {rising_range} archived:false fork:false"))
    # Fresh scouts deliberately sort by activity, not popularity, and use a low
    # floor. This is the lane that can catch a creator before a breakout.
    for frontier, query in frontiers[:8]:
        fresh_ceiling = f"..{min(max_stars, 999)}" if max_stars else "..999"
        specs.append(SearchSpec(f"fresh/{frontier}", f"{query} created:>={ninety_days_ago} stars:3{fresh_ceiling} archived:false fork:false", "updated"))
    return specs


def append_filters(spec: SearchSpec, *, language: str | None, max_age_days: int, now: datetime, max_stars: int = 0) -> SearchSpec:
    suffixes: list[str] = []
    if language:
        suffixes.append(f"language:{language}")
    if max_age_days:
        since = (now - timedelta(days=max_age_days)).date().isoformat()
        suffixes.append(f"created:>={since}")
    if max_stars:
        suffixes.append(f"stars:<={max_stars}")
    suffix = " " + " ".join(suffixes) if suffixes else ""
    return SearchSpec(spec.lane, spec.query + suffix, spec.sort)


WEB3_TERMS = (
    "web3", "blockchain", "crypto", "cryptocurrency", "defi", "onchain", "on-chain",
    "ethereum", "bitcoin", "solana", "token", "trading", "quant", "hedge fund",
    "hedge-fund", "portfolio", "market making", "market-making", "prediction market",
    "mev", "arbitrage", "forex", "stocks", "equities", "financial",
)
AI_TERMS = (
    "ai", "agent", "llm", "machine learning", "ml", "neural", "model", "autonomous",
    "copilot", "inference", "prediction", "reinforcement learning",
)


def is_focus_relevant(repo, focus: str) -> bool:
    """Filter README noise: relevance must appear in searchable repo metadata."""
    if focus == "general":
        return True
    haystack = " ".join((repo.full_name, repo.description, *repo.topics)).lower()
    return any(term in haystack for term in WEB3_TERMS) and any(term in haystack for term in AI_TERMS)
