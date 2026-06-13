"""Unified vector store: ChromaDB when available, FAISS fallback."""

from __future__ import annotations

import logging
import sys
from typing import Any, Protocol

from backend.core.llm_config import llm_settings

logger = logging.getLogger(__name__)

_chroma_available: bool | None = None


class VectorStoreProtocol(Protocol):
    def upsert_document(self, **kwargs: Any) -> bool: ...
    def search(self, query: str, top_k: int | None = None) -> list[dict]: ...
    def count(self) -> int: ...


def _chroma_works() -> bool:
    global _chroma_available
    if _chroma_available is not None:
        return _chroma_available
    if llm_settings.vector_backend == "faiss":
        _chroma_available = False
        return False
    if llm_settings.vector_backend == "auto" and sys.version_info >= (3, 14):
        logger.info("Python 3.14+ detected; using FAISS vector backend.")
        _chroma_available = False
        return False
    try:
        from backend.rag.chroma_store import get_chroma_store

        store = get_chroma_store()
        _chroma_available = store._ensure_collection() is not None
    except Exception:
        logger.warning("ChromaDB unavailable; using FAISS vector store.")
        _chroma_available = False
    return _chroma_available


def get_vector_store() -> VectorStoreProtocol:
    if _chroma_works():
        from backend.rag.chroma_store import get_chroma_store

        return get_chroma_store()
    from backend.rag.faiss_store import get_faiss_store

    return get_faiss_store()


def active_vector_backend() -> str:
    return "chromadb" if _chroma_works() else "faiss"
