from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from github_ai_radar.history import SnapshotStore
from test_ranking import repo


class HistoryTests(unittest.TestCase):
    def test_measures_star_delta_from_an_older_snapshot(self):
        now = datetime(2026, 9, 3, tzinfo=timezone.utc)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            payload = {
                "version": 1,
                "snapshots": [{
                    "captured_at": (now - timedelta(days=2)).isoformat(),
                    "repositories": {"org/tool": 80},
                }],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            observations = SnapshotStore(path).observations(
                [repo("org/tool", 100, "2026-01-01", "2026-09-02")], now
            )
            self.assertEqual(observations["org/tool"].delta, 20)
            self.assertEqual(observations["org/tool"].velocity, 10)

    def test_ignores_snapshot_less_than_six_hours_old(self):
        now = datetime(2026, 9, 3, tzinfo=timezone.utc)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            payload = {
                "version": 1,
                "snapshots": [{
                    "captured_at": (now - timedelta(hours=1)).isoformat(),
                    "repositories": {"org/tool": 80},
                }],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(SnapshotStore(path).observations(
                [repo("org/tool", 100, "2026-01-01", "2026-09-02")], now
            ), {})


if __name__ == "__main__":
    unittest.main()

