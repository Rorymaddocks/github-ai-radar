from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from unittest.mock import patch

from github_ai_radar.cli import build_queries, github_token


class QueryTests(unittest.TestCase):
    def test_filters_are_appended(self):
        args = SimpleNamespace(only_custom=True, query=["topic:ai"], language="Python", max_age_days=30)
        queries = build_queries(args, datetime(2026, 9, 3, tzinfo=timezone.utc))
        self.assertEqual(queries, ["topic:ai language:Python created:>=2026-08-04 stars:<=10000"])

    def test_custom_only_requires_query(self):
        args = SimpleNamespace(only_custom=True, query=[], language=None, max_age_days=0)
        with self.assertRaises(ValueError):
            build_queries(args, datetime(2026, 9, 3, tzinfo=timezone.utc))

    @patch.dict("os.environ", {"GITHUB_TOKEN": "explicit"})
    def test_explicit_token_takes_priority(self):
        self.assertEqual(github_token(), "explicit")


if __name__ == "__main__":
    unittest.main()
