from dataclasses import dataclass, field

import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier


REQUIRED_COLUMNS = ["heart_rate", "sleep_hours", "steps"]


def _validate_frame(data: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return data[REQUIRED_COLUMNS].copy()


@dataclass
class HealthPatternDetector:
    contamination: float = 0.15
    random_state: int = 42
    anomaly_model: IsolationForest = field(init=False)
    risk_model: RandomForestClassifier = field(init=False)

    def __post_init__(self) -> None:
        self.anomaly_model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self.risk_model = RandomForestClassifier(
            n_estimators=100,
            random_state=self.random_state,
        )

    def detect_anomalies(self, data: pd.DataFrame) -> pd.DataFrame:
        features = _validate_frame(data)
        model_output = self.anomaly_model.fit_predict(features)

        result = data.copy()
        result["anomaly_flag"] = [prediction == -1 for prediction in model_output]
        result["anomaly_score"] = self.anomaly_model.score_samples(features)
        return result

    def train_activity_risk_model(self, data: pd.DataFrame) -> None:
        features = _validate_frame(data)
        labels = (
            (features["heart_rate"] > 100)
            | (features["sleep_hours"] < 6)
            | (features["steps"] < 4000)
        ).astype(int)

        if labels.nunique() == 1:
            synthetic_row = pd.DataFrame(
                [
                    {
                        "heart_rate": 110 if labels.iloc[0] == 0 else 70,
                        "sleep_hours": 5.0 if labels.iloc[0] == 0 else 8.0,
                        "steps": 2500 if labels.iloc[0] == 0 else 9000,
                    }
                ]
            )
            features = pd.concat([features, synthetic_row], ignore_index=True)
            labels = pd.concat([labels, pd.Series([1 - int(labels.iloc[0])])], ignore_index=True)

        self.risk_model.fit(features, labels)

    def predict_activity_risk(self, data: pd.DataFrame) -> pd.DataFrame:
        if not hasattr(self.risk_model, "classes_"):
            self.train_activity_risk_model(data)

        features = _validate_frame(data)
        probabilities = self.risk_model.predict_proba(features)[:, 1]

        result = data.copy()
        result["activity_risk_score"] = probabilities.round(3)
        result["activity_risk_label"] = [
            "high" if score >= 0.6 else "moderate" if score >= 0.3 else "low"
            for score in probabilities
        ]
        return result


pattern_detector = HealthPatternDetector()
