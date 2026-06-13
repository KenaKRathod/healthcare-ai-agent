from dataclasses import dataclass, field

import pandas as pd
from sklearn.linear_model import LogisticRegression


REQUIRED_COLUMNS = ["bmi", "heart_rate", "steps"]
INDIAN_OVERWEIGHT_BMI = 23.0
INDIAN_OBESE_BMI = 25.0
IDRS_COLUMNS = ["age", "waist_cm", "activity", "family_diabetic"]


def _validate_frame(data: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return data[REQUIRED_COLUMNS].copy()


def _build_training_targets(features: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "diabetes_risk": ((features["bmi"] >= INDIAN_OBESE_BMI) | (features["steps"] < 4500)).astype(int),
        "cardiovascular_risk": (
            (features["heart_rate"] >= 95) | (features["bmi"] >= INDIAN_OVERWEIGHT_BMI)
        ).astype(int),
        "obesity_risk": ((features["bmi"] >= INDIAN_OBESE_BMI) | (features["steps"] < 5000)).astype(int),
    }


def _normalize_choice(value: str | None) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _idrs_risk_level(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def calculate_idrs(
    age: int | float,
    waist_cm: int | float,
    activity: str,
    family_diabetic: str,
    sex: str = "male",
) -> dict[str, int | str | dict[str, int]]:
    age_value = float(age)
    waist_value = float(waist_cm)
    normalized_activity = _normalize_choice(activity)
    normalized_family = _normalize_choice(family_diabetic)
    normalized_sex = _normalize_choice(sex)

    if age_value < 35:
        age_points = 0
    elif age_value < 50:
        age_points = 20
    else:
        age_points = 30

    waist_threshold = 80 if normalized_sex in {"female", "f", "woman"} else 90
    waist_points = 10 if waist_value >= waist_threshold else 0

    vigorous_values = {"vigorous", "regular", "vigorous_regular", "active"}
    moderate_values = {"moderate", "moderately_active"}
    sedentary_values = {"sedentary", "none", "no_activity", "inactive"}
    if normalized_activity in vigorous_values:
        activity_points = 0
    elif normalized_activity in moderate_values:
        activity_points = 10
    elif normalized_activity in sedentary_values:
        activity_points = 20
    else:
        raise ValueError("activity must be vigorous/regular, moderate, or sedentary/none.")

    no_family_values = {"no", "none", "zero", "no_parent", "no_parent_diabetic"}
    one_family_values = {"one", "single", "one_parent", "one_parent_diabetic"}
    both_family_values = {"both", "two", "both_parents", "both_parents_diabetic"}
    if normalized_family in no_family_values:
        family_points = 0
    elif normalized_family in one_family_values:
        family_points = 10
    elif normalized_family in both_family_values:
        family_points = 20
    else:
        raise ValueError("family_diabetic must be no, one, or both.")

    components = {
        "age": age_points,
        "waist": waist_points,
        "activity": activity_points,
        "family_history": family_points,
    }
    score = sum(components.values())
    return {
        "score": score,
        "risk_level": _idrs_risk_level(score),
        "components": components,
    }


def _has_idrs_inputs(row: pd.Series) -> bool:
    return all(column in row.index and not pd.isna(row[column]) for column in IDRS_COLUMNS)


@dataclass
class HealthRiskPredictor:
    random_state: int = 42
    models: dict[str, LogisticRegression] = field(default_factory=dict)

    def train(self, data: pd.DataFrame) -> None:
        features = _validate_frame(data)
        targets = _build_training_targets(features)

        self.models = {}
        for target_name, target_values in targets.items():
            target_features = features.copy()
            target_labels = target_values.copy()

            if target_labels.nunique() == 1:
                synthetic_row = pd.DataFrame(
                    [
                        {
                            "bmi": 33.0 if target_labels.iloc[0] == 0 else 22.0,
                            "heart_rate": 102 if target_labels.iloc[0] == 0 else 72,
                            "steps": 3000 if target_labels.iloc[0] == 0 else 9000,
                        }
                    ]
                )
                target_features = pd.concat([target_features, synthetic_row], ignore_index=True)
                target_labels = pd.concat(
                    [target_labels, pd.Series([1 - int(target_labels.iloc[0])])],
                    ignore_index=True,
                )

            model = LogisticRegression(random_state=self.random_state, max_iter=1000)
            model.fit(target_features, target_labels)
            self.models[target_name] = model

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.models:
            self.train(data)

        features = _validate_frame(data)
        result = data.copy()

        for target_name, model in self.models.items():
            probabilities = model.predict_proba(features)[:, 1]
            result[f"{target_name}_score"] = probabilities.round(3)
            result[f"{target_name}_label"] = [
                "high" if score >= 0.65 else "moderate" if score >= 0.35 else "low"
                for score in probabilities
            ]

        idrs_scores: list[int | None] = []
        idrs_labels: list[str | None] = []
        idrs_details: list[dict | None] = []
        for _, row in result.iterrows():
            if _has_idrs_inputs(row):
                idrs = calculate_idrs(
                    age=row["age"],
                    waist_cm=row["waist_cm"],
                    activity=str(row["activity"]),
                    family_diabetic=str(row["family_diabetic"]),
                    sex=str(row.get("sex", "male")),
                )
                idrs_scores.append(int(idrs["score"]))
                idrs_labels.append(str(idrs["risk_level"]))
                idrs_details.append(idrs)
            else:
                idrs_scores.append(None)
                idrs_labels.append(None)
                idrs_details.append(None)

        if any(score is not None for score in idrs_scores):
            result["idrs_score"] = idrs_scores
            result["idrs_risk_level"] = idrs_labels
            result["idrs_details"] = idrs_details

        return result


health_risk_predictor = HealthRiskPredictor()
