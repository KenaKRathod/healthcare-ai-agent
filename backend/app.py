from fastapi import FastAPI
from backend.routes import auth_routes
from backend.monitoring import REQUEST_COUNTER
from backend.database import engine
from backend.models import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)

@app.middleware("http")
async def count_requests(request, call_next):

    REQUEST_COUNTER.inc()

    response = await call_next(request)

    return response


@app.get("/")
def home():

    return {"message": "Healthcare AI Agent Running"}