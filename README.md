# Healthcare AI Agent

Healthcare-focused FastAPI backend featuring a modular LangGraph agent, rule-based ML risk scoring (IDRS), and built-in vitals analytics endpoints.

## Technology Stack

- **FastAPI** & **Uvicorn** for the REST API layer
- **LangGraph** & **OpenAI API** for the intelligent clinical agent orchestration
- **SQLAlchemy** supporting local **SQLite** (`health_data.db`) and production **PostgreSQL** (e.g., Supabase with IPv4 poolers)
- **Pandas** & **Altair** for analytics and vitals visualization
- **Hybrid Vector Database (RAG)**: Uses **ChromaDB** by default, with a fallback to **FAISS**, and a secondary fallback to pure **NumPy / Scikit-Learn** (TF-IDF cosine similarity) to ensure 100% startup and search resilience on serverless/cloud platforms.

## Project Structure

```text
healthcare-ai-agent
|
+-- backend
|   +-- agents          # LangGraph clinical decision trees
|   +-- api             # FastAPI API endpoints (patient, auth, chatbot, etc.)
|   +-- core            # Database models, configuration, and security settings
|   +-- ml              # Indian Diabetes Risk Score (IDRS) and risk models
|   +-- schemas         # Pydantic schemas for requests/responses
|   +-- services        # Business logic (goal management, RAG seeders)
|   +-- rag             # Vector stores (Chroma, FAISS, and NumPy fallbacks)
|   +-- app.py          # FastAPI application initialization and startup scripts
|   +-- requirements.txt# Pinned python package dependencies
\-- tests               # Automated test suite (Pytest)
```

## Setup & Run

### 1. Install Dependencies
Ensure you are using **Python 3.12** (pinned in `runtime.txt` to guarantee C extension compatibility for psycopg2 and numpy).

```bash
venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

### 2. Environment Configuration (`.env`)
Create a `.env` file in the root directory:

```env
# Database Settings (use sqlite locally, postgresql:// in production)
DATABASE_URL=sqlite:///backend/data/health_data.db
SECRET_KEY=your_secret_jwt_key_here
ALGORITHM=HS256
APP_NAME="Healthcare AI Agent"
APP_VERSION="0.1.0"

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# Vector Store Preferences (auto | chromadb | faiss)
VECTOR_BACKEND=auto
```

### 3. Run the Backend API
Start the local server:

```bash
venv\Scripts\python.exe -m uvicorn backend.app:app --reload
```

### 4. Running the Tests
To verify all features work correctly:

```bash
venv\Scripts\python.exe -m pytest
```

## Database Migration & Deployment Notes

- **Supabase/PostgreSQL poolers**: If deploying to Render (which has outbound IPv6 routing limits), route database connections using Supabase's IPv4 connection poolers (port 5432). Configure the username format as `[username].[project_id]` in the `DATABASE_URL` connection string so the shared pooler resolves your tenant correctly.
- **RAG Startup Resilience**: The startup script automatically builds the vector indices. If ChromaDB or FAISS encounters compiled binary loading issues on Render, the system will fall back to a NumPy/Scikit-Learn similarity matrix search, guaranteeing the server starts successfully without crashing.
