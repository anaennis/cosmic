import os
import tempfile
import unittest

from src.digest import format_authors, render_html, render_markdown, write_digest

HEADER = {'date': '2026-10-13', 'categories': ['astro-ph.GA', 'astro-ph.CO'],
          'interests': 'globular clusters'}
RESULTS = [{
    'metadata': {'id': 'http://arxiv.org/abs/2610.00001v1',
                 'title': 'Clusters at $z>2$ & <beyond>',
                 'authors': ['A. One', 'B. Two', 'C. Three', 'D. Four']},
    'similarity': 0.4567,
    'summary': 'We find <many> clusters.',
}]


class TestFormatAuthors(unittest.TestCase):
    def test_short_list(self):
        self.assertEqual(format_authors(['A', 'B']), 'A, B')

    def test_long_list(self):
        self.assertEqual(format_authors(['A', 'B', 'C', 'D']), 'A, B, C et al.')


class TestRender(unittest.TestCase):
    def test_markdown(self):
        md = render_markdown(RESULTS, HEADER)
        self.assertIn('# Cosmic digest — 2026-10-13', md)
        self.assertIn('astro-ph.GA, astro-ph.CO', md)
        self.assertIn('## [Clusters at $z>2$ & <beyond>](http://arxiv.org/abs/2610.00001v1)', md)
        self.assertIn('A. One, B. Two, C. Three et al.', md)
        self.assertIn('relevance 0.46', md)
        self.assertIn('We find <many> clusters.', md)

    def test_html_escapes_text(self):
        page = render_html(RESULTS, HEADER)
        self.assertIn('<a href="http://arxiv.org/abs/2610.00001v1">', page)
        self.assertIn('Clusters at $z&gt;2$ &amp; &lt;beyond&gt;', page)
        self.assertIn('We find &lt;many&gt; clusters.', page)
        self.assertNotIn('<many>', page)

    def test_empty_results(self):
        self.assertIn('Cosmic digest', render_markdown([], HEADER))
        self.assertIn('Cosmic digest', render_html([], HEADER))


class TestWriteDigest(unittest.TestCase):
    def test_format_follows_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            md_path = os.path.join(tmp, 'digest.md')
            html_path = os.path.join(tmp, 'digest.HTML')
            write_digest(md_path, RESULTS, HEADER)
            write_digest(html_path, RESULTS, HEADER)
            with open(md_path, encoding='utf-8') as f:
                self.assertTrue(f.read().startswith('# Cosmic digest'))
            with open(html_path, encoding='utf-8') as f:
                self.assertTrue(f.read().startswith('<!doctype html>'))


if __name__ == '__main__':
    unittest.main()
