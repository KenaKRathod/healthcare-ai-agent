"""ChromaDB vector store for medical RAG (non-PHI corpus only)."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from backend.core.llm_config import llm_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "medical_knowledge"
_store: "MedicalChromaStore | None" = None


class MedicalChromaStore:
    def __init__(self, persist_path: Path) -> None:
        self.persist_path = persist_path
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.persist_path))
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except Exception:
            logger.exception("ChromaDB initialization failed.")
            return None

    @staticmethod
    def doc_id(content_hash: str, chunk_index: int = 0) -> str:
        return f"{content_hash}_{chunk_index}"

    def upsert_document(
        self,
        *,
        content: str,
        content_hash: str,
        title: str,
        source: str,
        chunk_index: int = 0,
        extra_metadata: dict[str, Any] | None = None,
    ) -> bool:
        collection = self._ensure_collection()
        if collection is None:
            return False
        metadata = {
            "title": title[:500],
            "source": source[:120],
            "content_hash": content_hash,
            "chunk_index": chunk_index,
        }
        if extra_metadata:
            metadata.update({k: str(v)[:500] for k, v in extra_metadata.items()})
        try:
            collection.upsert(
                ids=[self.doc_id(content_hash, chunk_index)],
                documents=[content],
                metadatas=[metadata],
            )
            return True
        except Exception:
            logger.exception("ChromaDB upsert failed for %s", title)
            return False

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        collection = self._ensure_collection()
        if collection is None:
            return []
        limit = top_k or llm_settings.rag_top_k
        try:
            count = collection.count()
            if count == 0:
                return []
            results = collection.query(query_texts=[query], n_results=min(limit, count))
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]
            chunks = []
            for idx, doc in enumerate(documents):
                if not doc:
                    continue
                meta = metadatas[idx] if idx < len(metadatas) else {}
                distance = distances[idx] if idx < len(distances) else None
                score = round(1 - float(distance), 4) if distance is not None else None
                chunks.append(
                    {
                        "id": ids[idx] if idx < len(ids) else None,
                        "source": meta.get("source", "unknown"),
                        "title": meta.get("title", "Medical reference"),
                        "content": doc,
                        "score": score,
                    }
                )
            return chunks
        except Exception:
            logger.exception("ChromaDB search failed.")
            return []

    def count(self) -> int:
        collection = self._ensure_collection()
        if collection is None:
            return 0
        try:
            return collection.count()
        except Exception:
            return 0


def get_chroma_store() -> MedicalChromaStore:
    global _store
    if _store is None:
        base = Path(__file__).resolve().parents[1] / "data" / "chroma_medical"
        custom = llm_settings.chroma_persist_path
        path = Path(custom) if custom else base
        _store = MedicalChromaStore(path)
    return _store


def content_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
