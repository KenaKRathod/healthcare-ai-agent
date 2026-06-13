from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base
import sqlalchemy.types as types

from backend.core.security import encrypt_data, decrypt_data

Base = declarative_base()


class EncryptedString(types.TypeDecorator):
    """SQLAlchemy type that encrypts strings on write and decrypts on read."""
    impl = types.String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_data(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_data(value)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)  # patient, doctor, caregiver


class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True)
    heart_rate = Column(Integer)
    blood_pressure = Column(String)
    fasting_blood_sugar = Column(Float, nullable=True)
    postprandial_blood_sugar = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    waist_cm = Column(Float, nullable=True)
    activity = Column(String, nullable=True)
    family_diabetic = Column(String, nullable=True)
    idrs_score = Column(Integer, nullable=True)
    idrs_risk_level = Column(String, nullable=True)


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
    fasting_blood_sugar = Column(Float, nullable=False, default=0.0)
    postprandial_blood_sugar = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String, nullable=False, default="unknown")
    risk_score = Column(Float, nullable=False, default=0.0)
    anomaly_count = Column(Integer, nullable=False, default=0)
    idrs_score = Column(Integer, nullable=True)
    idrs_risk_level = Column(String, nullable=True)


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    height = Column(Float)
    weight = Column(Float)
    dietary_preference = Column(String)  # e.g., Vegetarian, Vegan, Non-Vegetarian
    state = Column(EncryptedString)  # Encrypted text PII
    pincode = Column(EncryptedString)  # Encrypted text PII
    waist_cm = Column(Float)
    physical_activity = Column(String)
    family_history = Column(String)


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    drug_name = Column(String, nullable=False)
    dosage = Column(String)
    timing = Column(String)  # e.g., Morning, Afternoon, Evening, Night
    drug_type = Column(String)  # e.g., Allopathic, Ayurvedic
    status = Column(String, default="Active")  # e.g., Active, Inactive


class MedicationAdherence(Base):
    __tablename__ = "medication_adherence"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    drug_name = Column(String, nullable=False)
    date = Column(String)  # Store as YYYY-MM-DD
    status = Column(String)  # e.g., Taken, Missed


class HealthInsurance(Base):
    __tablename__ = "health_insurances"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    provider_name = Column(EncryptedString, nullable=False)  # Encrypted text PII
    policy_number = Column(EncryptedString)  # Encrypted text PII
    coverage_limit = Column(Float)
    emergency_contact = Column(EncryptedString)  # Encrypted text PII


class DoctorConsultation(Base):
    __tablename__ = "doctor_consultations"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    doctor_name = Column(String, nullable=False)
    specialty = Column(String)
    date_visited = Column(String)  # Store as YYYY-MM-DD
    recommendations = Column(String)
    next_followup = Column(String)  # Store as YYYY-MM-DD


class HealthAlert(Base):
    __tablename__ = "health_alerts"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String, index=True, nullable=False)
    vital_type = Column(String, nullable=False)  # e.g., blood_pressure, blood_sugar, heart_rate
    value = Column(String)
    risk_level = Column(String)  # e.g., critical, warning
    message = Column(String)
    generated_at = Column(String)  # Store as YYYY-MM-DD HH:MM:SS


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(String, index=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    action = Column(String, nullable=False)  # e.g., READ, WRITE, EXPORT, LOGIN
    resource = Column(String, nullable=False)  # e.g., PatientProfile:John Doe, HealthData:all
    status = Column(String, nullable=False)  # e.g., SUCCESS, DENIED


class MedicalKnowledgeChunk(Base):
    __tablename__ = "medical_knowledge_chunks"

    id = Column(Integer, primary_key=True)
    source = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    content_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(String, nullable=False)


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    patient_name = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    health_context_json = Column(EncryptedString, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, index=True, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(EncryptedString, nullable=False)
    intent = Column(String, nullable=True)
    selected_tool = Column(String, nullable=True)
    metadata_json = Column(String, nullable=True)
    created_at = Column(String, nullable=False)


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    query = Column(EncryptedString, nullable=True)
    response = Column(EncryptedString, nullable=True)
    rating = Column(Integer, nullable=False)  # -1 thumbs down, 1 thumbs up
    comment = Column(EncryptedString, nullable=True)
    created_at = Column(String, nullable=False)
