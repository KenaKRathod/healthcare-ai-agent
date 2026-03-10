# Healthcare AI Agent

Healthcare-focused FastAPI backend with a modular LangGraph agent, rule-based ML risk scoring, and built-in vitals analytics endpoints.

## Stack

- FastAPI and Uvicorn for the API layer
- LangGraph for agent orchestration
- SQLAlchemy and SQLite/PostgreSQL for persistence
- Pandas and Altair for health data analysis and visualization
- Optional `scikit-learn` support for Python versions below 3.14

## Project Structure

```text
healthcare-ai-agent
|
+-- backend
|   +-- agents
|   +-- api
|   +-- core
|   +-- ml
|   +-- schemas
|   +-- services
|   +-- tools
|   +-- app.py
|   +-- auth.py
|   +-- database.py
|   +-- models.py
|   \-- requirements.txt
\-- tests
```

## Setup

1. Install dependencies

```bash
venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

2. Configure `.env`

```env
DATABASE_URL=sqlite:///backend/data/health_data.db
SECRET_KEY=healthcaresecret
ALGORITHM=HS256
APP_NAME=Healthcare AI Agent
APP_VERSION=0.1.0
```

3. Start the API

```bash
venv\Scripts\python.exe -m uvicorn backend.app:app --reload
```

## Available Endpoints

- `POST /health-data`
- `GET /health-data`
- `POST /ai-health-chat`
- `GET /analytics/risk-summary`
- `GET /analytics/vitals-chart`

## Notes

- The current environment uses Python 3.14.3, so the included ML layer defaults to a lightweight built-in risk model instead of requiring `scikit-learn`.
- Legacy imports such as `backend.routes.patient_routes` and `backend.health_agent` still work as compatibility shims.
