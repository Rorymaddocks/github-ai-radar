from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .github import GitHubClient, GitHubError
from .ranking import rank_all
from .report import render_terminal, write_json, write_markdown


DEFAULT_QUERIES = (
    "topic:ai-agents stars:>50 archived:false",
    "topic:autonomous-agents stars:>50 archived:false",
    "topic:agent-framework stars:>50 archived:false",
    '"AI agent" in:name,description,readme stars:>100 archived:false',
    '"LLM agent" in:name,description,readme stars:>100 archived:false',
    '"coding agent" in:name,description,readme stars:>50 archived:false',
    "topic:rag stars:>500 archived:false",
    "topic:llmops stars:>200 archived:false",
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Discover useful, high-star and rising AI projects on GitHub.")
    result.add_argument("--limit", type=int, default=25, help="number of results to display (default: 25)")
    result.add_argument("--per-query", type=int, default=30, help="repositories fetched per search query (default: 30)")
    result.add_argument("--min-stars", type=int, default=50, help="discard repositories below this count")
    result.add_argument("--max-age-days", type=int, default=0, help="only include repos created within N days; 0 disables")
    result.add_argument("--language", help="filter by GitHub language, e.g. Python or TypeScript")
    result.add_argument("--query", action="append", default=[], help="additional GitHub search query; may be repeated")
    result.add_argument("--only-custom", action="store_true", help="run only queries supplied with --query")
    result.add_argument("--json", type=Path, help="write all ranked results as JSON")
    result.add_argument("--markdown", type=Path, help="write the displayed results as Markdown")
    result.add_argument("--no-cache", action="store_true", help="ignore cached API responses")
    return result


def build_queries(args: argparse.Namespace, now: datetime) -> list[str]:
    queries = [] if args.only_custom else list(DEFAULT_QUERIES)
    queries.extend(args.query)
    if not queries:
        raise ValueError("At least one --query is required with --only-custom")
    suffixes = []
    if args.language:
        suffixes.append(f"language:{args.language}")
    if args.max_age_days:
        since = (now - timedelta(days=args.max_age_days)).date().isoformat()
        suffixes.append(f"created:>={since}")
    suffix = " " + " ".join(suffixes) if suffixes else ""
    return [query + suffix for query in queries]


def github_token() -> str:
    """Use an explicit token first, then the credential stored by GitHub CLI."""
    if token := os.environ.get("GITHUB_TOKEN", ""):
        return token
    if not shutil.which("gh"):
        return ""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.limit < 1 or not 1 <= args.per_query <= 100 or args.min_stars < 0 or args.max_age_days < 0:
        parser().error("limits and star/age values must be positive (per-query maximum is 100)")
    now = datetime.now(timezone.utc)
    try:
        queries = build_queries(args, now)
    except ValueError as exc:
        parser().error(str(exc))

    client = GitHubClient(
        token=github_token(),
        cache_dir=Path(".radar-cache"),
        cache_ttl_seconds=0 if args.no_cache else 3600,
    )
    found = {}
    try:
        for query in queries:
            for repo in client.search(query, per_page=args.per_query):
                if repo.stars >= args.min_stars:
                    found[repo.full_name.lower()] = repo
    except GitHubError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    ranked = rank_all(list(found.values()), now=now)
    print(render_terminal(ranked, args.limit))
    if args.json:
        write_json(ranked, args.json)
        print(f"\nWrote JSON: {args.json}")
    if args.markdown:
        write_markdown(ranked, args.markdown, generated_at=now, limit=args.limit)
        print(f"Wrote Markdown: {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
