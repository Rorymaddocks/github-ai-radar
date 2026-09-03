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
ESTABLISHED = (
    "topic:ai-agents stars:>1000",
    "topic:agent-framework stars:>1000",
    '"coding agent" in:name,description stars:>1000',
    "topic:rag stars:>2000",
    "topic:llmops stars:>1000",
)

FRONTIERS = (
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


def default_specs(now: datetime) -> list[SearchSpec]:
    year_ago = (now - timedelta(days=365)).date().isoformat()
    ninety_days_ago = (now - timedelta(days=90)).date().isoformat()
    specs = [SearchSpec("established", f"{query} archived:false fork:false") for query in ESTABLISHED]
    for frontier, query in FRONTIERS:
        specs.append(SearchSpec(f"rising/{frontier}", f"{query} created:>={year_ago} stars:15..9999 archived:false fork:false"))
    # Fresh scouts deliberately sort by activity, not popularity, and use a low
    # floor. This is the lane that can catch a creator before a breakout.
    for frontier, query in FRONTIERS[:8]:
        specs.append(SearchSpec(f"fresh/{frontier}", f"{query} created:>={ninety_days_ago} stars:3..999 archived:false fork:false", "updated"))
    return specs


def append_filters(spec: SearchSpec, *, language: str | None, max_age_days: int, now: datetime) -> SearchSpec:
    suffixes: list[str] = []
    if language:
        suffixes.append(f"language:{language}")
    if max_age_days:
        since = (now - timedelta(days=max_age_days)).date().isoformat()
        suffixes.append(f"created:>={since}")
    suffix = " " + " ".join(suffixes) if suffixes else ""
    return SearchSpec(spec.lane, spec.query + suffix, spec.sort)
