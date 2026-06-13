# AuraHealth AI — LLM, ChromaDB RAG, Memory & Feedback

Step-by-step integration on the existing FastAPI + LangGraph + PostgreSQL + React stack.

---

## Architecture

```text
User (React Chatbot)
  → POST /ai-health-chat
      → Conversation memory (PostgreSQL, encrypted)
      → Health context builder (vitals, profile, goals)
      → LangGraph:
          1. detect_intent (LLM router → rule fallback)
          2. select_tool
          3. retrieve_rag_context (ChromaDB)
          4. run_health_analysis (existing tools)
          5. run_ml_analysis
          6. build_insights → generate_report → compose_response (LLM + RAG)
      → Save assistant message
  ← response + conversation_id + message_id + rag_sources

Feedback
  → POST /ai-health-chat/feedback { message_id, rating: 1|-1 }
      → Stores query, response, rating, timestamp (encrypted PHI fields)
```

---

## Step 1 — Environment

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/healthcare_ai
ENCRYPTION_KEY=your-fernet-key

LLM_ENABLED=true
OPENAI_API_KEY=sk-your-key
LLM_MODEL=gpt-4o-mini
LLM_ROUTER_MODEL=gpt-4o-mini
USE_LLM_INTENT_ROUTER=true

RAG_TOP_K=4
CHROMA_PERSIST_PATH=backend/data/chroma_medical
```

```bash
pip install -r backend/requirements.txt
```

---

## Step 2 — Database migration

**Dev:** tables/columns auto-created on startup.

**Production PostgreSQL:**

```bash
psql -U postgres -d healthcare_ai -f backend/migrations/001_ai_conversation_rag.sql
psql -U postgres -d healthcare_ai -f backend/migrations/002_rag_memory_feedback.sql
```

| Table | Purpose |
|-------|---------|
| `medical_knowledge_chunks` | Document registry (non-PHI) |
| `chat_conversations` | Sessions + encrypted `health_context_json` |
| `chat_messages` | Encrypted user/assistant turns |
| `chat_feedback` | query, response, rating, timestamp |

Vector index (non-PHI corpus):
- **ChromaDB** at `backend/data/chroma_medical/` when compatible (Python ≤ 3.13)
- **FAISS** at `backend/data/faiss_medical/` auto-selected on Python 3.14+ or when Chroma fails

Set `VECTOR_BACKEND=faiss` or `VECTOR_BACKEND=chromadb` to force a backend.

---

## Step 3 — Ingest medical documents

Built-in guidelines seed on startup. Add PDFs/guidelines:

```bash
# Single PDF or text file
python -m backend.scripts.ingest_medical_documents --file path/to/guideline.pdf

# Entire folder of PDF/TXT/MD files
python -m backend.scripts.ingest_medical_documents --directory backend/data/medical_docs

# PubMed abstracts + Chroma sync
python -m backend.scripts.seed_medical_rag --pubmed-query "hypertension guidelines"
```

---

## Step 4 — LangGraph workflow (unchanged graph shape, new nodes)

| Node | File | Behavior |
|------|------|----------|
| `detect_intent` | `intent_router.py` | LLM JSON router → keyword fallback |
| `select_tool` | `intent_router.py` | Maps intent → existing tool |
| `retrieve_rag_context` | `medical_rag_service.py` | ChromaDB vector search |
| `run_health_analysis` | existing tools | symptoms, meds, nutrition, etc. |
| `compose_response` | `llm_service.py` | LLM answer using RAG + memory + tools |

---

## Step 5 — API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai-health-chat` | Chat with memory + RAG + LLM |
| GET | `/conversations` | List user sessions |
| GET | `/conversations/{id}/messages` | Reload encrypted history |
| POST | `/ai-health-chat/feedback` | Thumbs up/down + query/response log |

---

## Step 6 — Run

```bash
python -m uvicorn backend.app:app --reload
cd frontend && npm run dev
```

---

## Step 7 — Security

- Chat messages, feedback query/response, and health context are **Fernet-encrypted** at rest.
- RAG corpus contains **general medical knowledge only** — never patient PHI.
- RBAC: patients chat only as themselves; users rate only their own messages.
- Audit logs on chat access and feedback writes.
- LLM + router prompts enforce non-diagnostic guardrails.
- Graceful fallback: no API key → rule router + template responses; empty Chroma → TF-IDF fallback.

---

## Step 8 — Verify

1. Chat twice in one session — second answer should reference prior context.
2. Check API response: `intent_router_used: "llm"` or `"rules"`, `rag_sources` populated.
3. Rate a response — confirm `chat_feedback` row has `query`, `response`, `rating`, `created_at`.
4. Ingest a PDF and ask a question related to its content — verify retrieval in `rag_sources`.
