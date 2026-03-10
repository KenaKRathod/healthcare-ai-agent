DEFAULT_GOALS = {
    "daily_steps": 10000,
    "weight_loss_kg": 5,
    "sleep_hours": 8,
}


def progress_percentage(current_value: float, target_value: float) -> float:
    if target_value <= 0:
        raise ValueError("target_value must be positive.")
    return round(min((current_value / target_value) * 100, 100), 2)


def goal_recommendation(goal_name: str, current_value: float, target_value: float) -> str:
    progress = progress_percentage(current_value, target_value)

    if progress >= 100:
        return f"You have achieved your {goal_name} goal. Keep maintaining your routine."
    if progress >= 75:
        return f"You are close to your {goal_name} goal. Stay consistent and keep building momentum."
    if progress >= 40:
        return f"You are making progress on your {goal_name} goal. Small daily improvements will help."
    return f"Your {goal_name} goal needs more attention. Consider a simpler daily habit to get started."
