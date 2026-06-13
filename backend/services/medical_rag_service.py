import hashlib
from datetime import datetime
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from backend.core.llm_config import llm_settings
from backend.models import MedicalKnowledgeChunk
from backend.rag.chroma_store import content_hash
from backend.rag.vector_store import get_vector_store
from backend.rag.document_loader import chunk_text, iter_documents, load_document

SYSTEM_PROMPT_SOURCES = [
    {
        "source": "guidelines",
        "title": "Hypertension overview",
        "content": (
            "Hypertension is persistently elevated blood pressure that increases cardiovascular risk. "
            "First-line management often includes lifestyle changes, sodium reduction, regular exercise, "
            "and clinician-guided medication when indicated."
        ),
    },
    {
        "source": "guidelines",
        "title": "Type 2 diabetes monitoring",
        "content": (
            "Type 2 diabetes requires long-term glucose monitoring, nutrition planning, physical activity, "
            "and medication adherence. Indian Diabetes Risk Score (IDRS) can help stratify risk in screening contexts."
        ),
    },
    {
        "source": "guidelines",
        "title": "Asthma management",
        "content": (
            "Asthma is a chronic inflammatory airway disease. Controller therapy, rescue inhaler use as prescribed, "
            "and trigger avoidance are core management pillars."
        ),
    },
    {
        "source": "safety",
        "title": "Medical disclaimer",
        "content": (
            "AuraHealth AI provides educational health information only. It does not diagnose, prescribe, "
            "or replace licensed clinical care. Users with emergencies should contact local emergency services."
        ),
    },
    {
        "source": "medication",
        "title": "Drug interaction caution",
        "content": (
            "Always verify medication and herb interactions with a licensed pharmacist or physician. "
            "Common concerns include anticoagulants with NSAIDs and some Ayurvedic herbs."
        ),
    },
]


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def _index_chunk_in_chroma(
    *,
    content: str,
    content_hash_value: str,
    title: str,
    source: str,
    chunk_index: int = 0,
    file_name: str | None = None,
) -> bool:
    store = get_vector_store()
    return store.upsert_document(
        content=content,
        content_hash=content_hash_value,
        title=title,
        source=source,
        chunk_index=chunk_index,
        extra_metadata={"file_name": file_name} if file_name else None,
    )


def upsert_chunk(db: Session, source: str, title: str, content: str) -> MedicalKnowledgeChunk:
    digest = _content_hash(content)
    existing = (
        db.query(MedicalKnowledgeChunk)
        .filter(MedicalKnowledgeChunk.content_hash == digest)
        .first()
    )
    if existing:
        _index_chunk_in_chroma(
            content=content,
            content_hash_value=digest,
            title=title,
            source=source,
        )
        return existing

    chunk = MedicalKnowledgeChunk(
        source=source,
        title=title,
        content=content,
        content_hash=digest,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    _index_chunk_in_chroma(
        content=content,
        content_hash_value=digest,
        title=title,
        source=source,
    )
    return chunk


def seed_default_knowledge(db: Session) -> int:
    inserted = 0
    for item in SYSTEM_PROMPT_SOURCES:
        digest = _content_hash(item["content"])
        exists = (
            db.query(MedicalKnowledgeChunk)
            .filter(MedicalKnowledgeChunk.content_hash == digest)
            .first()
        )
        if exists:
            _index_chunk_in_chroma(
                content=item["content"],
                content_hash_value=digest,
                title=item["title"],
                source=item["source"],
            )
            continue
        db.add(
            MedicalKnowledgeChunk(
                source=item["source"],
                title=item["title"],
                content=item["content"],
                content_hash=digest,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        inserted += 1
    if inserted:
        db.commit()

    for item in SYSTEM_PROMPT_SOURCES:
        digest = _content_hash(item["content"])
        _index_chunk_in_chroma(
            content=item["content"],
            content_hash_value=digest,
            title=item["title"],
            source=item["source"],
        )
    return inserted


def sync_chroma_from_database(db: Session) -> int:
    """Rebuild Chroma index from PostgreSQL/SQLite chunk registry."""
    chunks = db.query(MedicalKnowledgeChunk).order_by(MedicalKnowledgeChunk.id.asc()).all()
    synced = 0
    for chunk in chunks:
        if _index_chunk_in_chroma(
            content=chunk.content,
            content_hash_value=chunk.content_hash,
            title=chunk.title,
            source=chunk.source,
        ):
            synced += 1
    return synced


def ingest_document_file(db: Session, file_path: Path) -> int:
    """Ingest a single PDF/TXT/MD file into Postgres registry + ChromaDB."""
    source_label, raw_text = load_document(file_path)
    chunks = chunk_text(raw_text)
    if not chunks:
        return 0

    inserted = 0
    for index, chunk_content in enumerate(chunks):
        digest = content_hash(f"{file_path.name}:{index}:{chunk_content}")
        title = f"{file_path.stem} (part {index + 1})"
        before = db.query(MedicalKnowledgeChunk).filter(MedicalKnowledgeChunk.content_hash == digest).count()
        upsert_chunk(db, source=source_label, title=title, content=chunk_content)
        get_vector_store().upsert_document(
            content=chunk_content,
            content_hash=digest,
            title=title,
            source=source_label,
            chunk_index=index,
            extra_metadata={"file_name": file_path.name},
        )
        after = db.query(MedicalKnowledgeChunk).filter(MedicalKnowledgeChunk.content_hash == digest).count()
        if after > before:
            inserted += 1
    return inserted


def ingest_documents_directory(db: Session, directory: Path) -> dict[str, int]:
    summary: dict[str, int] = {}
    for file_path in iter_documents(directory):
        summary[file_path.name] = ingest_document_file(db, file_path)
    return summary


def search_medical_context_vector(query: str, top_k: int | None = None) -> list[dict]:
    """Primary retriever: ChromaDB or FAISS vector search."""
    return get_vector_store().search(query, top_k=top_k)


def _search_medical_context_tfidf(db: Session, query: str, top_k: int) -> list[dict]:
    chunks = db.query(MedicalKnowledgeChunk).order_by(MedicalKnowledgeChunk.id.asc()).all()
    if not chunks:
        return []

    corpus = [chunk.content for chunk in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
    matrix = vectorizer.fit_transform(corpus)
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix).flatten()
    ranked = sorted(zip(chunks, scores), key=lambda item: item[1], reverse=True)[:top_k]

    results = []
    for chunk, score in ranked:
        if score <= 0:
            continue
        results.append(
            {
                "id": chunk.id,
                "source": chunk.source,
                "title": chunk.title,
                "content": chunk.content,
                "score": round(float(score), 4),
            }
        )
    return results


def search_medical_context(db: Session, query: str, top_k: int | None = None) -> list[dict]:
    """Retrieve medical context: ChromaDB first, TF-IDF fallback."""
    limit = top_k or llm_settings.rag_top_k
    vector_results = search_medical_context_vector(query, top_k=limit)
    if vector_results:
        return vector_results

    if db.query(MedicalKnowledgeChunk).count() == 0:
        seed_default_knowledge(db)
        sync_chroma_from_database(db)
        vector_results = search_medical_context_vector(query, top_k=limit)
        if vector_results:
            return vector_results

    return _search_medical_context_tfidf(db, query, limit)


def format_rag_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No retrieved medical references."
    lines = []
    for chunk in chunks:
        lines.append(
            f"[{chunk['source']}] {chunk['title']} (relevance={chunk.get('score', 'n/a')}): {chunk['content']}"
        )
    return "\n".join(lines)


def ingest_pubmed_abstracts(db: Session, query: str, max_results: int = 3) -> int:
    from backend.tools.research_tool import fetch_pubmed_abstracts

    articles = fetch_pubmed_abstracts(query, max_results=max_results)
    inserted = 0
    for article in articles:
        content = (
            f"Title: {article.get('title', 'Unknown')}. "
            f"Journal: {article.get('journal', 'Unknown')} ({article.get('year', 'n/a')}). "
            f"Abstract: {article.get('abstract', 'No abstract available.')}"
        )
        before = db.query(MedicalKnowledgeChunk).count()
        upsert_chunk(
            db,
            source="pubmed",
            title=str(article.get("title", "PubMed article"))[:250],
            content=content,
        )
        after = db.query(MedicalKnowledgeChunk).count()
        if after > before:
            inserted += 1
    return inserted
