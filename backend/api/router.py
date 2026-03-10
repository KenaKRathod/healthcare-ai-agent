from fastapi import APIRouter

from backend.api.routes import agent, analytics, auth, doctor, goals, health, reporting

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(doctor.router, tags=["doctor"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(agent.router, tags=["agent"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(analytics.health_analytics_router, tags=["analytics"])
api_router.include_router(reporting.router, tags=["reports"])
api_router.include_router(goals.router, tags=["goals"])
