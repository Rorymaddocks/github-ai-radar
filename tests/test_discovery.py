from datetime import datetime, timezone
import unittest

from github_ai_radar.discovery import default_specs


class DiscoveryTests(unittest.TestCase):
    def test_default_scan_has_multiple_cohorts(self):
        specs = default_specs(datetime(2026, 9, 3, tzinfo=timezone.utc))
        self.assertEqual(len(specs), 23)
        self.assertTrue(any(spec.lane == "established" for spec in specs))
        self.assertTrue(any(spec.lane.startswith("rising/") for spec in specs))
        self.assertTrue(any(spec.lane.startswith("fresh/") for spec in specs))

    def test_emerging_cohorts_have_star_ceilings(self):
        specs = default_specs(datetime(2026, 9, 3, tzinfo=timezone.utc))
        rising = [spec for spec in specs if spec.lane.startswith("rising/")]
        fresh = [spec for spec in specs if spec.lane.startswith("fresh/")]
        self.assertTrue(all("stars:15..9999" in spec.query for spec in rising))
        self.assertTrue(all("stars:3..999" in spec.query for spec in fresh))
        self.assertTrue(all(spec.sort == "updated" for spec in fresh))


if __name__ == "__main__":
    unittest.main()
