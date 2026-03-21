from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class HealthData(Base):

    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    heart_rate = Column(Integer)
    blood_pressure = Column(String)


class HealthGoal(Base):

    __tablename__ = "health_goals"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    goal_name = Column(String, nullable=False)
    target_value = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="")


class HealthJourneySnapshot(Base):

    __tablename__ = "health_journey_snapshots"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    heart_rate = Column(Float, nullable=False, default=0.0)
    systolic_bp = Column(Float, nullable=False, default=120.0)
    diastolic_bp = Column(Float, nullable=False, default=80.0)
    steps = Column(Float, nullable=False, default=0.0)
    sleep_hours = Column(Float, nullable=False, default=0.0)
    calorie_intake = Column(Float, nullable=False, default=0.0)
    bmi = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String, nullable=False, default="unknown")
    risk_score = Column(Float, nullable=False, default=0.0)
    anomaly_count = Column(Integer, nullable=False, default=0)
