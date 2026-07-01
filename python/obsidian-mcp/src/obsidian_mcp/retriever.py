"""Hybrid BM25 + vector retriever over the indexed vault."""
import json
import sqlite3
from pathlib import Path

import numpy as np
from model2vec import StaticModel
from rank_bm25 import BM25Okapi


class HybridRetriever:
    def __init__(self, db_path: str, vault_path: str) -> None:
        self.db_path = db_path
        self.vault_path = Path(vault_path)
        self.model = StaticModel.from_pretrained("minishlab/potion-base-8M")
        self._load()

    def _load(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, file_path, section_heading, chunk_text, tokens, embedding FROM chunks"
        ).fetchall()
        conn.close()

        self.chunks = [dict(r) for r in rows]

        if not self.chunks:
            self.embeddings_normed = np.zeros((0, 256), dtype=np.float32)
            self.bm25 = BM25Okapi([[]])
            return

        raw = np.array(
            [np.frombuffer(c["embedding"], dtype=np.float32) for c in self.chunks]
        )
        norms = np.linalg.norm(raw, axis=1, keepdims=True) + 1e-10
        self.embeddings_normed = raw / norms

        corpus = [json.loads(c["tokens"]) for c in self.chunks]
        self.bm25 = BM25Okapi(corpus)

    def reload(self) -> None:
        """Reload index from DB (call after incremental reindex)."""
        self._load()

    def search(self, query: str, limit: int = 5, max_tokens: int = 2000) -> list[dict]:
        if not self.chunks:
            return []

        # BM25
        bm25_scores = self.bm25.get_scores(query.lower().split())
        bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

        # Vector
        q_vec = self.model.encode([query])[0].astype(np.float32)
        q_vec /= np.linalg.norm(q_vec) + 1e-10
        cos_scores = self.embeddings_normed @ q_vec
        vec_ranked = sorted(range(len(cos_scores)), key=lambda i: cos_scores[i], reverse=True)

        # RRF fusion (k=60)
        pool = limit * 4
        rrf: dict[int, float] = {}
        for rank, idx in enumerate(bm25_ranked[:pool]):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (60 + rank + 1)
        for rank, idx in enumerate(vec_ranked[:pool]):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (60 + rank + 1)

        top = sorted(rrf, key=rrf.__getitem__, reverse=True)[:limit]

        results: list[dict] = []
        char_budget = max_tokens * 4
        used = 0

        for idx in top:
            chunk = self.chunks[idx]
            text = chunk["chunk_text"]
            remaining = char_budget - used
            if remaining <= 0:
                break
            if len(text) > remaining:
                text = text[:remaining]
            results.append(
                {
                    "file_path": chunk["file_path"],
                    "section": chunk["section_heading"],
                    "chunk_text": text,
                    "score": rrf[idx],
                }
            )
            used += len(text)

        return results
