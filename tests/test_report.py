from datetime import datetime, timezone
import unittest

from github_ai_radar.report import render_terminal, select_sections
from github_ai_radar.ranking import rank
from test_ranking import repo


NOW = datetime(2026, 9, 3, tzinfo=timezone.utc)


class ReportTests(unittest.TestCase):
    def test_hidden_gems_get_a_guaranteed_section(self):
        popular = rank(repo("big/riser", 9000, "2026-01-01", "2026-09-02"), now=NOW)
        gem = rank(repo("new/gem", 50, "2026-08-01", "2026-09-02"), now=NOW)
        sections = dict(select_sections([popular, gem], 10, "emerging"))
        self.assertIn("Hidden gems", sections)
        self.assertEqual(sections["Hidden gems"][0].repository.full_name, "new/gem")

    def test_default_report_does_not_show_creator_links(self):
        item = rank(repo("new/gem", 50, "2026-08-01", "2026-09-02"), now=NOW)
        output = render_terminal([item], [], 10, "emerging")
        self.assertNotIn("Emerging creators", output)
        self.assertIn("https://github.com/new/gem", output)


if __name__ == "__main__":
    unittest.main()
