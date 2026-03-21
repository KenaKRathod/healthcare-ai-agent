from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.schemas.health import GoalStatus, HealthGoalCreate, HealthGoalUpdate
from backend.services.goal_service import (
    build_goal_statuses,
    create_goal,
    list_patient_goals,
    update_goal_target,
)

router = APIRouter()


@router.get("/health-goals", response_model=list[GoalStatus])
def get_health_goals(
    db: Annotated[Session, Depends(get_db)],
    patient_name: str = "Unknown",
    steps: int = 0,
    sleep_hours: float = 0.0,
    weight_loss_progress_kg: float = 0.0,
):
    goals = list_patient_goals(db, patient_name)
    progress_inputs = {
        "daily_steps": float(steps),
        "sleep_hours": float(sleep_hours),
        "weight_loss_kg": float(weight_loss_progress_kg),
    }
    return [GoalStatus(**status) for status in build_goal_statuses(goals, progress_inputs)]


@router.post("/health-goals", response_model=GoalStatus)
def create_health_goal(
    payload: HealthGoalCreate,
    db: Annotated[Session, Depends(get_db)],
):
    goal = create_goal(
        db,
        patient_name=payload.patient_name,
        goal_name=payload.goal_name,
        target_value=payload.target_value,
        unit=payload.unit,
    )
    status = build_goal_statuses([goal], {payload.goal_name: 0.0})[0]
    return GoalStatus(**status)


@router.put("/health-goals/{goal_id}", response_model=GoalStatus)
def update_health_goal(
    goal_id: int,
    payload: HealthGoalUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    goal = update_goal_target(
        db,
        goal_id=goal_id,
        target_value=payload.target_value,
        unit=payload.unit,
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    status = build_goal_statuses([goal], {goal.goal_name: 0.0})[0]
    return GoalStatus(**status)
