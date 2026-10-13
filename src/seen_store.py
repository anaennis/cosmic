import json
import os
import re


def paper_key(paper_id):
    """Normalizes an arXiv ID URL so later versions (v2, v3...) count as the same paper."""
    return re.sub(r'v\d+$', '', paper_id.rstrip('/').split('/abs/')[-1])


class SeenStore:
    """Remembers which papers have already been shown, in a small JSON file."""

    def __init__(self, path):
        self.path = path
        self.seen = set()
        if os.path.exists(path):
            with open(path) as f:
                self.seen = set(json.load(f))

    def is_seen(self, paper):
        return paper_key(paper['id']) in self.seen

    def mark_seen(self, papers):
        self.seen.update(paper_key(p['id']) for p in papers)

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(sorted(self.seen), f, indent=2)
