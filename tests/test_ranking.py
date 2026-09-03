from datetime import datetime, timezone
import unittest

from github_ai_radar.models import Repository
from github_ai_radar.ranking import classify, rank, rank_all


NOW = datetime(2026, 9, 3, tzinfo=timezone.utc)


def repo(name: str, stars: int, created: str, updated: str, **overrides) -> Repository:
    values = dict(
        full_name=name,
        html_url=f"https://github.com/{name}",
        description="A production-ready AI agent framework",
        stars=stars,
        forks=100,
        open_issues=10,
        language="Python",
        topics=("ai-agents", "agent-framework"),
        license="MIT",
        created_at=datetime.fromisoformat(created).replace(tzinfo=timezone.utc),
        updated_at=datetime.fromisoformat(updated).replace(tzinfo=timezone.utc),
        archived=False,
        homepage="https://example.com",
        owner_login=name.split("/", 1)[0],
        owner_url=f"https://github.com/{name.split('/', 1)[0]}",
        owner_type="Organization",
        pushed_at=datetime.fromisoformat(updated).replace(tzinfo=timezone.utc),
        is_fork=False,
    )
    values.update(overrides)
    return Repository(**values)


class RankingTests(unittest.TestCase):
    def test_fast_recent_project_scores_well(self):
        item = rank(repo("org/fast", 5000, "2026-08-01", "2026-09-02"), now=NOW)
        self.assertGreater(item.score, 70)
        self.assertIn("recently active", item.reasons)

    def test_archived_project_is_penalized(self):
        active = repo("org/active", 5000, "2026-01-01", "2026-09-02")
        archived = repo("org/archived", 5000, "2026-01-01", "2026-09-02", archived=True)
        self.assertGreater(rank(active, now=NOW).score, rank(archived, now=NOW).score)

    def test_resource_lists_are_penalized(self):
        tool = repo("org/tool", 1000, "2026-01-01", "2026-09-02")
        listing = repo("org/awesome-ai-agents", 1000, "2026-01-01", "2026-09-02")
        self.assertGreater(rank(tool, now=NOW).score, rank(listing, now=NOW).score)

    def test_classifies_agent_framework(self):
        self.assertEqual(classify(repo("org/tool", 10, "2026-01-01", "2026-09-02")), "Agent framework")

    def test_rank_all_descending(self):
        items = [repo("org/old", 50, "2020-01-01", "2025-01-01"), repo("org/new", 5000, "2026-08-01", "2026-09-02")]
        ranked = rank_all(items, now=NOW)
        self.assertEqual(ranked[0].repository.full_name, "org/new")


if __name__ == "__main__":
    unittest.main()
