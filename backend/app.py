from fastapi import FastAPI
from backend.routes import auth_routes
from monitoring import REQUEST_COUNTER
from backend.routes import doctor_routes

app.include_router(doctor_routes.router)

app = FastAPI()

app.include_router(auth_routes.router)

@app.middleware("http")
async def count_requests(request, call_next):

    REQUEST_COUNTER.inc()

    response = await call_next(request)

    return response


@app.get("/")
def home():

    return {"message":"Healthcare AI Agent Running"}