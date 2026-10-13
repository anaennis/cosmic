import datetime
import unittest

import pytz

from src.arxiv_retriever import build_query_url, extract_arxiv_metadata, get_arxiv_dates

EASTERN = pytz.timezone('US/Eastern')


def eastern(year, month, day, hour):
    return EASTERN.localize(datetime.datetime(year, month, day, hour))


class TestGetArxivDates(unittest.TestCase):
    # October 2026: the 9th is a Friday, the 12th a Monday.

    def test_midweek_after_announcement(self):
        # Wednesday 21:00 -> Wednesday's batch (Tue 1400 -> Wed 1400)
        self.assertEqual(get_arxiv_dates(eastern(2026, 10, 14, 21)),
                         ('202610131400', '202610141400'))

    def test_midweek_before_announcement(self):
        # Wednesday 10:00 -> Tuesday's batch (Mon 1400 -> Tue 1400)
        self.assertEqual(get_arxiv_dates(eastern(2026, 10, 14, 10)),
                         ('202610121400', '202610131400'))

    def test_monday_batch_spans_weekend(self):
        # Monday 21:00 -> Monday's batch (Fri 1400 -> Mon 1400)
        self.assertEqual(get_arxiv_dates(eastern(2026, 10, 12, 21)),
                         ('202610091400', '202610121400'))

    def test_tuesday_before_announcement_uses_monday_batch(self):
        self.assertEqual(get_arxiv_dates(eastern(2026, 10, 13, 10)),
                         ('202610091400', '202610121400'))

    def test_weekend_uses_friday_batch(self):
        # Saturday and Sunday -> Friday's batch (Thu 1400 -> Fri 1400)
        for day in (10, 11):
            self.assertEqual(get_arxiv_dates(eastern(2026, 10, day, 12)),
                             ('202610081400', '202610091400'))

    def test_accepts_other_timezones(self):
        # 01:00 UTC Thursday is 21:00 ET Wednesday
        now = datetime.datetime(2026, 10, 15, 1, tzinfo=pytz.utc)
        self.assertEqual(get_arxiv_dates(now),
                         ('202610131400', '202610141400'))


class TestBuildQueryUrl(unittest.TestCase):
    def test_single_category(self):
        url = build_query_url('astro-ph.GA', '202610091400', '202610121400', 50)
        self.assertIn('search_query=cat:astro-ph.GA+AND+submittedDate:'
                      '[202610091400+TO+202610121400]', url)
        self.assertIn('max_results=50', url)

    def test_single_category_as_list(self):
        self.assertEqual(build_query_url(['astro-ph.GA'], 'a', 'b'),
                         build_query_url('astro-ph.GA', 'a', 'b'))

    def test_multiple_categories_are_grouped(self):
        url = build_query_url(['astro-ph.GA', 'astro-ph.CO'], 'a', 'b')
        self.assertIn('search_query=%28cat:astro-ph.GA+OR+cat:astro-ph.CO%29+AND+', url)


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2610.00001v1</id>
    <published>2026-10-09T17:58:27Z</published>
    <title>Globular Clusters
      in the Virgo Cluster</title>
    <summary>  We study
      globular clusters.  </summary>
    <author><name>A. Author</name></author>
    <author><name>B. Author</name></author>
    <category term="astro-ph.GA"/>
    <category term="astro-ph.CO"/>
  </entry>
</feed>"""


class TestExtractArxivMetadata(unittest.TestCase):
    def test_parses_and_cleans_entry(self):
        papers = extract_arxiv_metadata(SAMPLE_FEED)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper['title'], 'Globular Clusters in the Virgo Cluster')
        self.assertEqual(paper['abstract'], 'We study globular clusters.')
        self.assertEqual(paper['authors'], ['A. Author', 'B. Author'])
        self.assertEqual(paper['categories'], ['astro-ph.GA', 'astro-ph.CO'])
        self.assertEqual(paper['id'], 'http://arxiv.org/abs/2610.00001v1')

    def test_empty_feed(self):
        feed = '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        self.assertEqual(extract_arxiv_metadata(feed), [])


if __name__ == '__main__':
    unittest.main()
