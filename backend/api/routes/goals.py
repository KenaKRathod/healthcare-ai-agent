from fastapi import APIRouter

from backend.health_goals import DEFAULT_GOALS, goal_recommendation, progress_percentage
from backend.schemas.health import GoalStatus

router = APIRouter()


@router.get("/health-goals", response_model=list[GoalStatus])
def get_health_goals(
    steps: int = 0,
    sleep_hours: float = 0.0,
    weight_loss_progress_kg: float = 0.0,
):
    return [
        GoalStatus(
            goal_name="daily_steps",
            current_value=float(steps),
            target_value=float(DEFAULT_GOALS["daily_steps"]),
            progress_percent=progress_percentage(float(steps), float(DEFAULT_GOALS["daily_steps"])),
            recommendation=goal_recommendation(
                "daily_steps",
                float(steps),
                float(DEFAULT_GOALS["daily_steps"]),
            ),
        ),
        GoalStatus(
            goal_name="sleep_hours",
            current_value=float(sleep_hours),
            target_value=float(DEFAULT_GOALS["sleep_hours"]),
            progress_percent=progress_percentage(float(sleep_hours), float(DEFAULT_GOALS["sleep_hours"])),
            recommendation=goal_recommendation(
                "sleep_hours",
                float(sleep_hours),
                float(DEFAULT_GOALS["sleep_hours"]),
            ),
        ),
        GoalStatus(
            goal_name="weight_loss_kg",
            current_value=float(weight_loss_progress_kg),
            target_value=float(DEFAULT_GOALS["weight_loss_kg"]),
            progress_percent=progress_percentage(
                float(weight_loss_progress_kg),
                float(DEFAULT_GOALS["weight_loss_kg"]),
            ),
            recommendation=goal_recommendation(
                "weight_loss_kg",
                float(weight_loss_progress_kg),
                float(DEFAULT_GOALS["weight_loss_kg"]),
            ),
        ),
    ]
