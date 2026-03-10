def calculate_bmi(weight_kg: float, height_m: float) -> dict[str, float | str]:
    if weight_kg <= 0 or height_m <= 0:
        raise ValueError("Weight and height must be positive values.")

    bmi = round(weight_kg / (height_m**2), 2)
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "normal"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obese"

    return {"bmi": bmi, "category": category}


def track_steps(steps: int, goal_steps: int = 10000) -> dict[str, int | float | bool]:
    if steps < 0 or goal_steps <= 0:
        raise ValueError("Steps must be non-negative and goal_steps must be positive.")

    progress = round((steps / goal_steps) * 100, 2)
    return {
        "steps": steps,
        "goal_steps": goal_steps,
        "progress_percent": progress,
        "goal_reached": steps >= goal_steps,
    }


def calorie_burn(
    weight_kg: float,
    duration_minutes: int,
    activity_level: str = "moderate",
) -> dict[str, float | str]:
    if weight_kg <= 0 or duration_minutes <= 0:
        raise ValueError("Weight and duration must be positive values.")

    met_values = {
        "light": 3.0,
        "moderate": 5.0,
        "intense": 8.0,
    }
    met = met_values.get(activity_level.lower())
    if met is None:
        raise ValueError("activity_level must be light, moderate, or intense.")

    hours = duration_minutes / 60
    calories = round(met * weight_kg * hours, 2)
    return {
        "activity_level": activity_level.lower(),
        "duration_minutes": duration_minutes,
        "estimated_calories_burned": calories,
    }
