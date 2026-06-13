from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import get_current_user
from backend.models import User, HealthGoal
from backend.schemas.health import GoalStatus, HealthGoalCreate, HealthGoalUpdate
from backend.services.goal_service import (
    build_goal_statuses,
    create_goal,
    list_patient_goals,
    update_goal_target,
)
from backend.services.audit_service import log_audit_event

router = APIRouter()


@router.get("/health-goals", response_model=list[GoalStatus])
def get_health_goals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patient_name: str = "Unknown",
    steps: int = 0,
    sleep_hours: float = 0.0,
    weight_loss_progress_kg: float = 0.0,
):
    # Enforce RBAC: Patient can only view their own goals
    target_patient = patient_name
    if current_user.role == "patient":
        target_patient = current_user.username

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource=f"HealthGoal:{target_patient}",
        status="SUCCESS"
    )

    goals = list_patient_goals(db, target_patient)
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
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Enforce RBAC: Patient can only create goals for themselves
    if current_user.role == "patient" and current_user.username != payload.patient_name:
        log_audit_event(
            db,
            username=current_user.username,
            role=current_user.role,
            action="WRITE",
            resource=f"HealthGoal:{payload.patient_name}",
            status="DENIED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create health goals for yourself."
        )

    goal = create_goal(
        db,
        patient_name=payload.patient_name,
        goal_name=payload.goal_name,
        target_value=payload.target_value,
        unit=payload.unit,
    )
    
    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="WRITE",
        resource=f"HealthGoal:{payload.patient_name}:{payload.goal_name}",
        status="SUCCESS"
    )

    status_data = build_goal_statuses([goal], {payload.goal_name: 0.0})[0]
    return GoalStatus(**status_data)


@router.put("/health-goals/{goal_id}", response_model=GoalStatus)
def update_health_goal(
    goal_id: int,
    payload: HealthGoalUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Retrieve existing goal
    goal = db.query(HealthGoal).filter(HealthGoal.id == goal_id).first()
    if not goal:
        log_audit_event(
            db,
            username=current_user.username,
            role=current_user.role,
            action="WRITE",
            resource=f"HealthGoal:{goal_id}",
            status="NOT_FOUND"
        )
        raise HTTPException(status_code=404, detail="Goal not found")

    # Enforce RBAC: Patient can only edit their own goals
    if current_user.role == "patient" and current_user.username != goal.patient_name:
        log_audit_event(
            db,
            username=current_user.username,
            role=current_user.role,
            action="WRITE",
            resource=f"HealthGoal:{goal_id}",
            status="DENIED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not permitted to modify this goal."
        )

    updated_goal = update_goal_target(
        db,
        goal_id=goal_id,
        target_value=payload.target_value,
        unit=payload.unit,
    )

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="WRITE",
        resource=f"HealthGoal:{goal_id}",
        status="SUCCESS"
    )

    status_data = build_goal_statuses([updated_goal], {updated_goal.goal_name: 0.0})[0]
    return GoalStatus(**status_data)
