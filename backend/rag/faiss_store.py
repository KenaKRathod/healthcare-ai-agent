"""FAISS vector store for medical RAG (with pure NumPy/Scikit-Learn fallback)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from backend.core.llm_config import llm_settings

logger = logging.getLogger(__name__)

# Detect if FAISS library is available
_faiss_available = False
try:
    import faiss
    _faiss_available = True
except BaseException:
    logger.warning("FAISS binary is not available. Falling back to NumPy/Scikit-Learn for vector search.")

_store: MedicalFaissStore | None = None


class MedicalFaissStore:
    def __init__(self, persist_path: Path) -> None:
        self.persist_path = persist_path
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.persist_path / "medical.index"
        self.meta_file = self.persist_path / "metadata.json"
        self.vectorizer_file = self.persist_path / "vectorizer.json"
        self._index = None
        self._metadata: list[dict] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._load()

    def _load(self) -> None:
        if self.meta_file.exists():
            try:
                self._metadata = json.loads(self.meta_file.read_text(encoding="utf-8"))
            except Exception:
                logger.exception("Failed to load FAISS metadata.")
                self._metadata = []
        if _faiss_available and self.index_file.exists():
            try:
                import faiss
                self._index = faiss.read_index(str(self.index_file))
            except BaseException:
                logger.exception("Failed to load FAISS index.")
                self._index = None

    def _save_metadata(self) -> None:
        try:
            self.meta_file.write_text(json.dumps(self._metadata, ensure_ascii=True), encoding="utf-8")
        except Exception:
            logger.exception("Failed to save FAISS metadata.")

    def _save_index(self, matrix) -> None:
        if not _faiss_available:
            return
        try:
            import faiss
            dim = matrix.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(matrix.astype(np.float32))
            faiss.write_index(index, str(self.index_file))
            self._index = index
        except BaseException:
            logger.exception("Failed to save FAISS index.")
            self._index = None

    def _rebuild(self) -> None:
        if not self._metadata:
            self._index = None
            if self.index_file.exists():
                try:
                    self.index_file.unlink()
                except Exception:
                    pass
            return

        try:
            corpus = [item["content"] for item in self._metadata]
            vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
            matrix = vectorizer.fit_transform(corpus)
            dense = normalize(matrix, norm="l2", axis=1).toarray()
            self._vectorizer = vectorizer
            if _faiss_available:
                self._save_index(dense)
            else:
                self._index = None
        except Exception:
            logger.exception("Failed to rebuild FAISS/vectorizer index.")

    def upsert_document(
        self,
        *,
        content: str,
        content_hash: str,
        title: str,
        source: str,
        chunk_index: int = 0,
        extra_metadata: dict | None = None,
    ) -> bool:
        doc_id = f"{content_hash}_{chunk_index}"
        for item in self._metadata:
            if item.get("doc_id") == doc_id:
                return True

        record = {
            "doc_id": doc_id,
            "content_hash": content_hash,
            "chunk_index": chunk_index,
            "title": title,
            "source": source,
            "content": content,
        }
        if extra_metadata:
            record.update(extra_metadata)
        self._metadata.append(record)
        self._save_metadata()
        self._rebuild()
        return True

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        limit = top_k or llm_settings.rag_top_k
        if not self._metadata:
            return []

        try:
            # Fit/transform query
            corpus = [item["content"] for item in self._metadata]
            vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
            matrix = vectorizer.fit_transform(corpus)
            query_vec = normalize(vectorizer.transform([query]), norm="l2", axis=1).toarray().astype(np.float32)

            if _faiss_available and self._index is not None:
                scores, indices = self._index.search(query_vec, min(limit, len(self._metadata)))
                scores_list = scores[0]
                indices_list = indices[0]
            else:
                # Cosine similarity using NumPy dot product
                dense_matrix = normalize(matrix, norm="l2", axis=1).toarray().astype(np.float32)
                similarities = (query_vec @ dense_matrix.T)[0]
                indices_list = np.argsort(similarities)[::-1][:limit]
                scores_list = similarities[indices_list]

            results = []
            for score, idx in zip(scores_list, indices_list):
                if idx < 0 or idx >= len(self._metadata):
                    continue
                meta = self._metadata[idx]
                results.append(
                    {
                        "id": meta.get("doc_id"),
                        "source": meta.get("source", "unknown"),
                        "title": meta.get("title", "Medical reference"),
                        "content": meta.get("content", ""),
                        "score": round(float(score), 4),
                    }
                )
            return results
        except Exception:
            logger.exception("FAISS/NumPy search failed.")
            return []

    def count(self) -> int:
        return len(self._metadata)


def get_faiss_store() -> MedicalFaissStore:
    global _store
    if _store is None:
        base = Path(__file__).resolve().parents[1] / "data" / "faiss_medical"
        custom = llm_settings.faiss_persist_path
        path = Path(custom) if custom else base
        _store = MedicalFaissStore(path)
    return _store
