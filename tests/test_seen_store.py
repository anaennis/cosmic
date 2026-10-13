import os
import tempfile
import unittest

from src.seen_store import SeenStore, paper_key


def paper(arxiv_id):
    return {'id': f'http://arxiv.org/abs/{arxiv_id}'}


class TestPaperKey(unittest.TestCase):
    def test_strips_url_and_version(self):
        self.assertEqual(paper_key('http://arxiv.org/abs/2610.13719v1'), '2610.13719')
        self.assertEqual(paper_key('http://arxiv.org/abs/2610.13719v12'), '2610.13719')

    def test_old_style_ids(self):
        self.assertEqual(paper_key('http://arxiv.org/abs/astro-ph/0601001v2'), 'astro-ph/0601001')


class TestSeenStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, 'seen.json')

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_missing_file_starts_empty(self):
        store = SeenStore(self.path)
        self.assertFalse(store.is_seen(paper('2610.00001v1')))

    def test_persists_across_instances(self):
        store = SeenStore(self.path)
        store.mark_seen([paper('2610.00001v1'), paper('2610.00002v1')])
        store.save()

        reloaded = SeenStore(self.path)
        self.assertTrue(reloaded.is_seen(paper('2610.00001v1')))
        self.assertTrue(reloaded.is_seen(paper('2610.00002v1')))
        self.assertFalse(reloaded.is_seen(paper('2610.00003v1')))

    def test_new_version_counts_as_seen(self):
        store = SeenStore(self.path)
        store.mark_seen([paper('2610.00001v1')])
        self.assertTrue(store.is_seen(paper('2610.00001v2')))


if __name__ == '__main__':
    unittest.main()
