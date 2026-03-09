import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.database import engine
from backend.models import Base
from backend.monitoring import REQUEST_COUNTER
from backend.routes import ai_routes, auth_routes, doctor_routes, patient_routes

app = FastAPI()
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)
app.include_router(doctor_routes.router)
app.include_router(patient_routes.router)
app.include_router(ai_routes.router)


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
