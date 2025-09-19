
import json
import re
from pathlib import Path
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi

_WORD_SPLIT = re.compile(r"[^a-zA-Z0-9äöüÄÖÜß]+")


def tokenize(text: str) -> List[str]:
    return [t for t in _WORD_SPLIT.split(text.lower()) if t]


class Retriever:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.docs: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25 = None
        self._load()

    def _load(self):
        self.docs.clear()
        self.corpus_tokens.clear()
        if not self.index_path.exists():
            return
        with open(self.index_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                self.docs.append(rec)
                self.corpus_tokens.append(tokenize(rec['text']))
        if self.docs:
            self.bm25 = BM25Okapi(self.corpus_tokens)

    def reload(self):
        self._load()

    def search(self, query: str, k: int = 5):
        if not self.docs or not self.bm25:
            return []
        q_tokens = tokenize(query)
        scores = self.bm25.get_scores(q_tokens)
        # top k indices
        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for i in idxs:
            doc = self.docs[i]
            results.append({
                'score': float(scores[i]),
                'text': doc['text'],
                'source_name': doc.get('source_name'),
                'source_path': doc.get('source_path'),
                'page': doc.get('page'),
                'chunk_idx': doc.get('chunk_idx'),
            })
        return results
