from collections.abc import Iterable

from sqlalchemy.orm import Session

from backend.health_goals import DEFAULT_GOALS, goal_recommendation, progress_percentage
from backend.models import HealthGoal


DEFAULT_GOAL_UNITS = {
    "daily_steps": "steps",
    "sleep_hours": "hours",
    "weight_loss_kg": "kg",
}


def _default_goal_rows(patient_name: str) -> list[HealthGoal]:
    return [
        HealthGoal(
            patient_name=patient_name,
            goal_name=goal_name,
            target_value=float(target_value),
            unit=DEFAULT_GOAL_UNITS.get(goal_name, ""),
        )
        for goal_name, target_value in DEFAULT_GOALS.items()
    ]


def ensure_patient_goals(db: Session, patient_name: str) -> list[HealthGoal]:
    goals = (
        db.query(HealthGoal)
        .filter(HealthGoal.patient_name == patient_name)
        .order_by(HealthGoal.id.asc())
        .all()
    )
    if goals:
        # Deduplicate any existing duplicate goals from previous bug
        seen = set()
        deduplicated = []
        to_delete = []
        for goal in goals:
            if goal.goal_name in seen:
                to_delete.append(goal)
            else:
                seen.add(goal.goal_name)
                deduplicated.append(goal)
        if to_delete:
            for goal in to_delete:
                db.delete(goal)
            db.commit()
            return deduplicated
        return goals

    goals = _default_goal_rows(patient_name)
    db.add_all(goals)
    db.commit()
    for goal in goals:
        db.refresh(goal)
    return goals


def list_patient_goals(db: Session, patient_name: str) -> list[HealthGoal]:
    return ensure_patient_goals(db, patient_name)


def create_goal(
    db: Session,
    patient_name: str,
    goal_name: str,
    target_value: float,
    unit: str,
) -> HealthGoal:
    existing_goal = (
        db.query(HealthGoal)
        .filter(
            HealthGoal.patient_name == patient_name,
            HealthGoal.goal_name == goal_name,
        )
        .first()
    )
    if existing_goal:
        existing_goal.target_value = float(target_value)
        existing_goal.unit = unit
        db.add(existing_goal)
        db.commit()
        db.refresh(existing_goal)
        return existing_goal

    goal = HealthGoal(
        patient_name=patient_name,
        goal_name=goal_name,
        target_value=float(target_value),
        unit=unit,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal_target(
    db: Session,
    goal_id: int,
    target_value: float | None = None,
    unit: str | None = None,
) -> HealthGoal | None:
    goal = db.query(HealthGoal).filter(HealthGoal.id == goal_id).first()
    if not goal:
        return None

    if target_value is not None:
        goal.target_value = float(target_value)
    if unit is not None:
        goal.unit = unit

    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def build_goal_statuses(
    goals: Iterable[HealthGoal],
    progress_inputs: dict[str, float],
) -> list[dict[str, float | str]]:
    statuses = []
    for goal in goals:
        current_value = float(progress_inputs.get(goal.goal_name, 0.0))
        statuses.append(
            {
                "goal_id": goal.id,
                "patient_name": goal.patient_name,
                "goal_name": goal.goal_name,
                "current_value": current_value,
                "target_value": float(goal.target_value),
                "unit": goal.unit,
                "progress_percent": progress_percentage(current_value, float(goal.target_value)),
                "recommendation": goal_recommendation(
                    goal.goal_name,
                    current_value,
                    float(goal.target_value),
                ),
            }
        )
    return statuses
