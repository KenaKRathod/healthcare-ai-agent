"""Load and chunk medical documents (PDF, TXT, MD) for RAG ingestion."""

from __future__ import annotations

from pathlib import Path


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        chunks.append(cleaned[start:end])
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf_file(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to ingest PDF documents.") from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def load_document(path: Path) -> tuple[str, str]:
    """Return (source_label, raw_text)."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf", load_pdf_file(path)
    if suffix in {".txt", ".md", ".csv"}:
        return suffix.lstrip("."), load_text_file(path)
    raise ValueError(f"Unsupported document type: {suffix}")


def iter_documents(directory: Path) -> list[Path]:
    patterns = ("*.pdf", "*.txt", "*.md")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(directory.glob(pattern)))
    return files
