from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _prepare_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_heart_rate_trends(data: pd.DataFrame, output_path: str | Path) -> str:
    chart_data = data.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"])

    plt.figure(figsize=(10, 4))
    plt.plot(chart_data["date"], chart_data["heart_rate"], marker="o", linewidth=2)
    plt.title("Heart Rate Trends")
    plt.xlabel("Date")
    plt.ylabel("Heart Rate (bpm)")
    plt.grid(alpha=0.3)
    plt.tight_layout()

    path = _prepare_output_path(output_path)
    plt.savefig(path)
    plt.close()
    return str(path)


def plot_steps_over_time(data: pd.DataFrame, output_path: str | Path) -> str:
    chart_data = data.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"])

    plt.figure(figsize=(10, 4))
    plt.bar(chart_data["date"], chart_data["steps"], color="#2E8B57")
    plt.title("Steps Over Time")
    plt.xlabel("Date")
    plt.ylabel("Steps")
    plt.tight_layout()

    path = _prepare_output_path(output_path)
    plt.savefig(path)
    plt.close()
    return str(path)


def plot_calorie_intake(data: pd.DataFrame, output_path: str | Path) -> str:
    chart_data = data.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"])

    plt.figure(figsize=(10, 4))
    plt.plot(chart_data["date"], chart_data["calorie_intake"], marker="s", color="#FF7F50")
    plt.title("Calorie Intake")
    plt.xlabel("Date")
    plt.ylabel("Calories")
    plt.tight_layout()

    path = _prepare_output_path(output_path)
    plt.savefig(path)
    plt.close()
    return str(path)


def plot_sleep_hours(data: pd.DataFrame, output_path: str | Path) -> str:
    chart_data = data.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"])

    plt.figure(figsize=(10, 4))
    plt.plot(chart_data["date"], chart_data["sleep_hours"], marker="^", color="#6A5ACD")
    plt.title("Sleep Hours")
    plt.xlabel("Date")
    plt.ylabel("Hours Slept")
    plt.tight_layout()

    path = _prepare_output_path(output_path)
    plt.savefig(path)
    plt.close()
    return str(path)
