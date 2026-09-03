from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .creators import rank_creators
from .discovery import SearchSpec, append_filters, default_specs, is_focus_relevant
from .github import GitHubClient, GitHubError
from .history import SnapshotStore
from .ranking import rank_all
from .report import render_terminal, write_json, write_markdown


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Discover established projects, AI breakouts, hidden gems, and emerging creators.")
    result.add_argument("--limit", type=int, default=20, help="results per report section (default: 20)")
    result.add_argument("--per-query", type=int, default=20, help="repositories fetched per search lane (default: 20)")
    result.add_argument("--min-stars", type=int, default=3, help="final global star floor (default: 3)")
    result.add_argument("--max-stars", type=int, default=10_000, help="maximum stars per result; 0 means unlimited (default: 10,000)")
    result.add_argument("--focus", choices=("web3", "general"), default="web3", help="discovery domain (default: web3)")
    result.add_argument("--max-age-days", type=int, default=0, help="only include repos created within N days; 0 disables")
    result.add_argument("--language", help="filter by GitHub language, e.g. Python or TypeScript")
    result.add_argument("--mode", choices=("all", "emerging", "established"), default="all")
    result.add_argument("--include-creators", action="store_true", help="also show creator/account analysis")
    result.add_argument("--quick", action="store_true", help="skip fresh activity-sorted lanes (15 instead of 23 searches)")
    result.add_argument("--query", action="append", default=[], help="additional GitHub search query; may be repeated")
    result.add_argument("--only-custom", action="store_true", help="run only queries supplied with --query")
    result.add_argument("--history", type=Path, default=Path(".radar-history.json"), help="snapshot file for true momentum")
    result.add_argument("--no-history", action="store_true", help="do not load or record star snapshots")
    result.add_argument("--creator-profiles", type=int, default=10, help="enrich this many emerging creators (default: 10)")
    result.add_argument("--json", type=Path, help="write repositories and creators as JSON")
    result.add_argument("--markdown", type=Path, help="write a shareable Markdown radar")
    result.add_argument("--no-cache", action="store_true", help="ignore cached API responses")
    return result


def build_specs(args: argparse.Namespace, now: datetime) -> list[SearchSpec]:
    specs = [] if args.only_custom else default_specs(
        now, focus=getattr(args, "focus", "web3"), max_stars=getattr(args, "max_stars", 10_000)
    )
    if getattr(args, "quick", False):
        specs = [spec for spec in specs if not spec.lane.startswith("fresh/")]
    specs.extend(SearchSpec("custom", query) for query in args.query)
    if not specs:
        raise ValueError("At least one --query is required with --only-custom")
    return [append_filters(
        spec,
        language=args.language,
        max_age_days=args.max_age_days,
        now=now,
        max_stars=getattr(args, "max_stars", 10_000),
    ) for spec in specs]


def build_queries(args: argparse.Namespace, now: datetime) -> list[str]:
    """Backward-compatible query view used by integrations and older callers."""
    return [spec.query for spec in build_specs(args, now)]


def github_token() -> str:
    """Use an explicit token first, then the credential stored by GitHub CLI."""
    if token := os.environ.get("GITHUB_TOKEN", ""):
        return token
    if not shutil.which("gh"):
        return ""
    try:
        result = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.limit < 1 or not 1 <= args.per_query <= 100 or args.min_stars < 0 or args.max_stars < 0 or args.max_age_days < 0 or args.creator_profiles < 0:
        parser().error("limits and star/age values must be positive (per-query maximum is 100)")
    now = datetime.now(timezone.utc)
    try:
        specs = build_specs(args, now)
    except ValueError as exc:
        parser().error(str(exc))

    client = GitHubClient(token=github_token(), cache_dir=Path(".radar-cache"), cache_ttl_seconds=0 if args.no_cache else 3600)
    found = {}
    lanes: dict[str, set[str]] = {}
    failures: list[str] = []
    for spec in specs:
        try:
            for repo in client.search(spec.query, per_page=args.per_query, sort=spec.sort):
                if (
                    repo.stars >= args.min_stars
                    and (not args.max_stars or repo.stars <= args.max_stars)
                    and is_focus_relevant(repo, args.focus)
                    and not repo.archived
                    and not repo.is_fork
                ):
                    key = repo.full_name.lower()
                    found[key] = repo
                    lanes.setdefault(key, set()).add(spec.lane)
        except GitHubError as exc:
            failures.append(f"{spec.lane}: {exc}")
            if "rate limit" in str(exc).lower():
                break

    if not found and failures:
        print(f"error: {failures[0]}", file=sys.stderr)
        return 1

    repositories = list(found.values())
    history = SnapshotStore(args.history)
    observations = {} if args.no_history else history.observations(repositories, now)
    ranked = rank_all(repositories, now=now, lanes=lanes, observations=observations)
    creators = []
    if args.include_creators:
        creators = rank_creators(ranked)
        profiles = {}
        emerging_creators = [creator for creator in creators if creator.breakout_projects]
        for creator in emerging_creators[: args.creator_profiles]:
            try:
                profiles[creator.login.lower()] = client.creator_profile(creator.login)
            except GitHubError as exc:
                failures.append(f"creator/{creator.login}: {exc}")
        if profiles:
            creators = rank_creators(ranked, profiles)
    visible_creators = creators
    print(render_terminal(ranked, visible_creators, args.limit, args.mode))
    if not args.no_history:
        history.record(repositories, now)
        if not observations:
            print(f"\nBaseline saved to {args.history}; a scan 6+ hours later enables observed momentum.")
    if args.json:
        write_json(ranked, visible_creators, args.json, generated_at=now)
        print(f"Wrote JSON: {args.json}")
    if args.markdown:
        write_markdown(ranked, visible_creators, args.markdown, generated_at=now, limit=args.limit, mode=args.mode)
        print(f"Wrote Markdown: {args.markdown}")
    if failures:
        print(f"\nCompleted with {len(failures)} warning(s):", file=sys.stderr)
        for failure in failures[:5]:
            print(f"  - {failure}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
