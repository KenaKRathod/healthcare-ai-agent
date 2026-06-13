"""Seed medical RAG knowledge and optionally ingest PubMed abstracts."""

import argparse

from backend.database import SessionLocal
from backend.services.medical_rag_service import (
    ingest_pubmed_abstracts,
    seed_default_knowledge,
    sync_chroma_from_database,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AuraHealth medical RAG corpus")
    parser.add_argument("--pubmed-query", default="", help="Optional PubMed query to ingest")
    parser.add_argument("--pubmed-limit", type=int, default=3)
    parser.add_argument("--sync-chroma", action="store_true", default=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        inserted = seed_default_knowledge(db)
        print(f"Inserted {inserted} default knowledge chunk(s).")
        if args.pubmed_query.strip():
            pubmed_inserted = ingest_pubmed_abstracts(
                db,
                query=args.pubmed_query.strip(),
                max_results=args.pubmed_limit,
            )
            print(f"Inserted {pubmed_inserted} PubMed chunk(s) for query: {args.pubmed_query}")
        if args.sync_chroma:
            synced = sync_chroma_from_database(db)
            print(f"Synced {synced} chunk(s) to ChromaDB.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
