def calorie_analysis(
    daily_calories: int,
    target_calories: int,
) -> dict[str, int | str]:
    if daily_calories < 0 or target_calories <= 0:
        raise ValueError("daily_calories must be non-negative and target_calories must be positive.")

    difference = daily_calories - target_calories
    if difference > 150:
        status = "above target"
    elif difference < -150:
        status = "below target"
    else:
        status = "on target"

    return {
        "daily_calories": daily_calories,
        "target_calories": target_calories,
        "difference": difference,
        "status": status,
    }


def nutrition_recommendation(goal: str) -> list[str]:
    plans = {
        "weight_loss": [
            "Prioritize high-fiber vegetables and lean protein.",
            "Reduce sugary drinks and late-night snacks.",
            "Use a moderate calorie deficit instead of crash dieting.",
        ],
        "muscle_gain": [
            "Increase protein intake across all meals.",
            "Add complex carbohydrates around workouts.",
            "Track hydration and recovery along with calories.",
        ],
        "maintenance": [
            "Keep meals balanced across protein, carbs, and healthy fats.",
            "Stay consistent with portion sizes.",
            "Use weekly averages instead of focusing on single meals.",
        ],
    }

    return plans.get(goal.lower(), ["Choose a goal such as weight_loss, muscle_gain, or maintenance."])


def diet_plan(goal: str) -> dict[str, list[str] | str]:
    templates = {
        "weight_loss": {
            "breakfast": ["Greek yogurt", "berries", "chia seeds"],
            "lunch": ["Grilled chicken salad", "olive oil dressing"],
            "dinner": ["Baked fish", "steamed vegetables", "brown rice"],
        },
        "muscle_gain": {
            "breakfast": ["Oats", "eggs", "banana"],
            "lunch": ["Rice", "chicken breast", "mixed vegetables"],
            "dinner": ["Salmon", "sweet potato", "avocado salad"],
        },
        "maintenance": {
            "breakfast": ["Whole-grain toast", "eggs", "fruit"],
            "lunch": ["Turkey wrap", "salad"],
            "dinner": ["Lean protein", "quinoa", "vegetables"],
        },
    }

    return templates.get(goal.lower(), {"message": "No diet plan found for the requested goal."})
