"""Ingest medical PDFs, guidelines, and text documents into ChromaDB + Postgres."""

import argparse
from pathlib import Path

from backend.database import SessionLocal
from backend.services.medical_rag_service import (
    ingest_document_file,
    ingest_documents_directory,
    seed_default_knowledge,
    sync_chroma_from_database,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest medical documents into AuraHealth RAG")
    parser.add_argument("--file", type=str, help="Path to a single PDF/TXT/MD file")
    parser.add_argument("--directory", type=str, help="Directory containing medical documents")
    parser.add_argument("--seed-defaults", action="store_true", help="Seed built-in guideline chunks")
    parser.add_argument("--sync-chroma", action="store_true", help="Sync Chroma index from database")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.seed_defaults:
            inserted = seed_default_knowledge(db)
            print(f"Seeded {inserted} default chunk(s).")

        if args.file:
            count = ingest_document_file(db, Path(args.file))
            print(f"Ingested {count} new chunk(s) from file: {args.file}")

        if args.directory:
            summary = ingest_documents_directory(db, Path(args.directory))
            print("Directory ingestion summary:")
            for name, count in summary.items():
                print(f"  - {name}: {count} new chunk(s)")

        if args.sync_chroma or not any([args.file, args.directory, args.seed_defaults]):
            synced = sync_chroma_from_database(db)
            print(f"Synced {synced} chunk(s) to ChromaDB.")

        if not any([args.file, args.directory, args.seed_defaults, args.sync_chroma]):
            print("No action selected. Use --file, --directory, --seed-defaults, or --sync-chroma.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
