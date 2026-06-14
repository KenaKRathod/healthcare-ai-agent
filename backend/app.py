import logging
import os
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from backend.api.router import api_router
from backend.core.config import settings
from backend.database import engine
from backend.models import Base
from backend.monitoring import REQUEST_COUNTER

app = FastAPI(title=settings.app_name, version=settings.app_version)
logger = logging.getLogger(__name__)

cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    for origin in re.split(r",\s*|\s+", env_origins):
        if origin:
            cors_origins.append(origin.strip().rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def _table_columns(table_name: str) -> set[str]:
    try:
        return {column["name"] for column in inspect(engine).get_columns(table_name)}
    except Exception:
        logger.warning("Skipping migration for missing table: %s", table_name)
        return set()


def ensure_ai_feature_columns() -> None:
    conversation_columns = _table_columns("chat_conversations")
    if conversation_columns and "health_context_json" not in conversation_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE chat_conversations ADD COLUMN health_context_json TEXT"))

    feedback_columns = _table_columns("chat_feedback")
    if feedback_columns:
        with engine.begin() as connection:
            if "query" not in feedback_columns:
                connection.execute(text("ALTER TABLE chat_feedback ADD COLUMN query TEXT"))
            if "response" not in feedback_columns:
                connection.execute(text("ALTER TABLE chat_feedback ADD COLUMN response TEXT"))


def seed_medical_rag_on_startup() -> None:
    try:
        from backend.database import SessionLocal
        from backend.services.medical_rag_service import seed_default_knowledge, sync_chroma_from_database

        db = SessionLocal()
        try:
            seed_default_knowledge(db)
            sync_chroma_from_database(db)
        finally:
            db.close()
    except BaseException:
        logger.exception("Medical RAG seed skipped due to startup error.")


def ensure_sqlite_health_data_columns() -> None:
    if not engine.url.drivername.startswith("sqlite"):
        return

    # 1. Health Data Table Migration
    existing_columns = _table_columns("health_data")
    new_columns = {
        "fasting_blood_sugar": "FLOAT",
        "postprandial_blood_sugar": "FLOAT",
        "age": "INTEGER",
        "sex": "VARCHAR",
        "waist_cm": "FLOAT",
        "activity": "VARCHAR",
        "family_diabetic": "VARCHAR",
        "idrs_score": "INTEGER",
        "idrs_risk_level": "VARCHAR",
    }
    with engine.begin() as connection:
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE health_data ADD COLUMN {column_name} {column_type}"))

    # 2. Patient Profiles Table Migration
    profile_columns = _table_columns("patient_profiles")
    new_profile_columns = {
        "waist_cm": "FLOAT",
        "physical_activity": "VARCHAR",
        "family_history": "VARCHAR",
    }
    with engine.begin() as connection:
        for column_name, column_type in new_profile_columns.items():
            if column_name not in profile_columns:
                connection.execute(text(f"ALTER TABLE patient_profiles ADD COLUMN {column_name} {column_type}"))

    # 3. Health Journey Snapshots Table Migration
    snapshot_columns = _table_columns("health_journey_snapshots")
    new_snapshot_columns = {
        "idrs_score": "INTEGER",
        "idrs_risk_level": "VARCHAR",
    }
    with engine.begin() as connection:
        for column_name, column_type in new_snapshot_columns.items():
            if column_name not in snapshot_columns:
                connection.execute(text(f"ALTER TABLE health_journey_snapshots ADD COLUMN {column_name} {column_type}"))


ensure_sqlite_health_data_columns()
ensure_ai_feature_columns()
seed_medical_rag_on_startup()

app.include_router(api_router)


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


@app.middleware("http")
async def count_requests(request: Request, call_next):
    REQUEST_COUNTER.inc()
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled exception for request path: %s", request.url.path)
        raise


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    errors = exc.errors()
    if errors:
        first_err = errors[0]
        # Extract the field location, ignoring the top-level 'body' wrapper
        loc = [str(x) for x in first_err.get("loc", []) if x != "body"]
        field_name = ".".join(loc)
        msg = first_err.get("msg", "Invalid value")
        detail = f"{field_name}: {msg}" if field_name else msg
        return error_response(detail, 422)
    return error_response("Invalid request payload.", 422)



@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    logger.warning("Value error on %s: %s", request.url.path, str(exc))
    return error_response(str(exc), 400)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error on %s", request.url.path)
    return error_response("A database error occurred.", 500)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application error on %s", request.url.path)
    return error_response("Internal server error.", 500)


@app.get("/")
def home():
    return {"message": "Healthcare AI Agent Running"}
