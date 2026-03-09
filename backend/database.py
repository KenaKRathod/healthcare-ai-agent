from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

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