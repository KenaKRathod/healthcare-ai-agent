from dataclasses import dataclass, field

import pandas as pd
from sklearn.linear_model import LogisticRegression


REQUIRED_COLUMNS = ["bmi", "heart_rate", "steps"]


def _validate_frame(data: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return data[REQUIRED_COLUMNS].copy()


def _build_training_targets(features: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "diabetes_risk": ((features["bmi"] >= 30) | (features["steps"] < 4500)).astype(int),
        "cardiovascular_risk": ((features["heart_rate"] >= 95) | (features["bmi"] >= 28)).astype(int),
        "obesity_risk": ((features["bmi"] >= 27) | (features["steps"] < 5000)).astype(int),
    }


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

        return result


health_risk_predictor = HealthRiskPredictor()
