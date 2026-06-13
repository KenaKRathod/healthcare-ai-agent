import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import SessionLocal
from backend.models import PatientProfile, HealthData, HealthAlert

client = TestClient(app)

def run_integration_tests():
    print("=== Testing FastAPI Endpoints (TestClient) ===")
    
    # 1. Setup Patient Profile in Database
    db = SessionLocal()
    patient_name = "KenaPatel"
    try:
        # Clear old test data
        db.query(PatientProfile).filter(PatientProfile.patient_name == patient_name).delete()
        db.query(HealthData).filter(HealthData.patient_name == patient_name).delete()
        db.query(HealthAlert).filter(HealthAlert.patient_name == patient_name).delete()
        db.commit()
        
        # Insert Patient Profile (Age 45, Male, Waist 95cm, Sedentary, family diabetic -> High IDRS)
        profile = PatientProfile(
            patient_name=patient_name,
            age=45,
            gender="male",
            height=1.75,
            weight=82.0,  # BMI = 26.7 (Calibrated as Obese for Indian guidelines >= 25)
            dietary_preference="Vegetarian",
            state="Gujarat",
            pincode="380001",
            waist_cm=95.0,
            physical_activity="sedentary",
            family_history="one"
        )
        db.add(profile)
        db.commit()
        print(f"Created patient profile for: {patient_name}")
        
    finally:
        db.close()

    # 2. Test POST /health-data (including fasting & postprandial sugar)
    print("\n--- Testing POST /health-data ---")
    data_payload = {
        "patient_name": patient_name,
        "heart_rate": 82,
        "blood_pressure": "120/80",
        "age": 45,
        "sex": "male",
        "waist_cm": 95.0,
        "activity": "sedentary",
        "family_diabetic": "one",
        "fasting_blood_sugar": 145.0,        # Elevated -> Hyperglycemia Warning
        "postprandial_blood_sugar": 160.0
    }
    
    # We pass query parameters because the endpoint expects query params for optional fields
    response = client.post(
        f"/health-data?patient_name={patient_name}&heart_rate=82&blood_pressure=120/80"
        f"&age=45&sex=male&waist_cm=95&activity=sedentary&family_diabetic=one"
        f"&fasting_blood_sugar=145&postprandial_blood_sugar=160"
    )
    
    print("Response status:", response.status_code)
    print("Response body:", response.json())
    assert response.status_code == 200
    assert "idrs_score" in response.json()
    assert response.json()["idrs_score"] == 60 
    # Wait, age: 35-49 is 20, waist: >=90 (male) is 10, activity: sedentary is 20, family: one is 10 -> Total 60.
    
    # 3. Test POST /ai-health-chat for Ayurvedic herb details
    print("\n--- Testing POST /ai-health-chat (Ayurveda intent) ---")
    chat_payload = {
        "question": "What is the Ayurvedic herb Ashwagandha used for?",
        "patient_name": patient_name
    }
    chat_response = client.post("/ai-health-chat", json=chat_payload)
    print("Response status:", chat_response.status_code)
    print("Response text excerpt:", chat_response.json()["response"][:200])
    assert chat_response.status_code == 200
    assert "Arjuna" in chat_response.json()["response"] or "Ashwagandha" in chat_response.json()["response"]
    
    # 4. Test POST /ai-health-chat with critical vitals causing real-time alert trigger
    print("\n--- Testing POST /ai-health-chat (Emergency alert trigger) ---")
    critical_chat_payload = {
        "question": "Help, what should I do?",
        "patient_name": patient_name,
        "latest_vitals": {
            "heart_rate": 90,
            "blood_pressure": "195/125"  # Hypertensive Crisis
        }
    }
    critical_response = client.post("/ai-health-chat", json=critical_chat_payload)
    print("Response status:", critical_response.status_code)
    print("Response text excerpt:", critical_response.json()["response"][:200])
    assert critical_response.status_code == 200
    assert "EMERGENCY" in critical_response.json()["response"]
    
    print("\nAll integration API endpoints verified successfully!")

if __name__ == "__main__":
    run_integration_tests()
