from datetime import datetime, timezone
import unittest

from github_ai_radar.creators import rank_creators
from github_ai_radar.ranking import rank
from test_ranking import repo


NOW = datetime(2026, 9, 3, tzinfo=timezone.utc)


class CreatorTests(unittest.TestCase):
    def test_creator_portfolio_is_aggregated(self):
        items = [
            rank(repo("maker/agent-one", 500, "2026-07-01", "2026-09-02"), now=NOW),
            rank(repo("maker/agent-two", 300, "2026-08-01", "2026-09-02"), now=NOW),
        ]
        creator = rank_creators(items)[0]
        self.assertEqual(creator.login, "maker")
        self.assertEqual(creator.discovered_repositories, 2)
        self.assertEqual(creator.total_stars, 800)


if __name__ == "__main__":
    unittest.main()
