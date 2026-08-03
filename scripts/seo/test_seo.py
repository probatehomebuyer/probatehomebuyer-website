import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from gsc_weekly_report import Period, complete_periods, opportunity_rows, report_markdown
from site_audit import load_page


class SeoAutomationTests(unittest.TestCase):
    def test_periods_exclude_latest_three_days_and_do_not_overlap(self):
        current, previous = complete_periods(date(2026, 8, 3))
        self.assertEqual((current.start.isoformat(), current.end.isoformat()), ("2026-07-04", "2026-07-31"))
        self.assertEqual((previous.start.isoformat(), previous.end.isoformat()), ("2026-06-06", "2026-07-03"))

    def test_existing_content_is_preferred_for_overlapping_query(self):
        current = [{"query": "sell inherited house needing work", "clicks": 1.0, "impressions": 200.0, "ctr": 0.005, "position": 12.0}]
        previous = [{"query": "sell inherited house needing work", "clicks": 0.0, "impressions": 100.0, "ctr": 0.0, "position": 18.0}]
        inventory = [{"url": "/sell-probate-property-needing-work/", "title": "Sell Probate Property Needing Work", "description": "Sell an inherited house that needs repairs", "h1s": ["Sell a probate property that needs work"], "intent": "commercial seller intent"}]
        result = opportunity_rows(current, previous, inventory)
        self.assertEqual(result[0]["action"], "improve existing page")
        self.assertEqual(result[0]["match"]["url"], "/sell-probate-property-needing-work/")

    def test_inventory_parses_visible_posted_date(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            article = root / "blog" / "example" / "index.html"
            article.parent.mkdir(parents=True)
            article.write_text(
                '<html><head><title>Example</title><meta name="description" content="Description">'
                '<link rel="canonical" href="https://probatehomebuyer.co.uk/blog/example/"></head>'
                '<body><h1>Example</h1><div class="article-date">Posted 9 June 2026</div></body></html>',
                encoding="utf-8",
            )
            page = load_page(article, root)
            self.assertEqual(page.publication_date, "2026-06-09")

    def test_weekly_markdown_report_renders(self):
        metric = {"clicks": 10.0, "impressions": 100.0, "ctr": 0.1, "position": 8.0}
        datasets = {
            "totals_current": [metric], "totals_previous": [{**metric, "clicks": 8.0}],
            "queries_current": [{"query": "sell inherited house", **metric}],
            "queries_previous": [{"query": "sell inherited house", **metric}],
            "pages_current": [{"page": "https://probatehomebuyer.co.uk/sell-inherited-house/", **metric}],
            "pages_previous": [{"page": "https://probatehomebuyer.co.uk/sell-inherited-house/", **metric}],
            "devices_current": [{"device": "MOBILE", **metric}], "devices_previous": [],
        }
        inventory = [{"url": "/sell-inherited-house/", "title": "Sell an inherited house", "description": "Direct inherited house sale", "h1s": ["Sell an inherited house"], "intent": "commercial seller intent", "internal_links": []}]
        report = report_markdown("sc-domain:probatehomebuyer.co.uk", Period(date(2026, 7, 4), date(2026, 7, 31)), Period(date(2026, 6, 6), date(2026, 7, 3)), datasets, inventory)
        self.assertIn("## Primary recommendation", report)
        self.assertIn("### Internal-linking opportunities", report)
        self.assertIn("Search Console property", report)


if __name__ == "__main__":
    unittest.main()
