import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal
from backend.services.alerts import check_and_trigger_alerts
from backend.models import HealthAlert

def test_alerts():
    print("=== Testing Real-Time Alerts & Database Logging ===")
    db = SessionLocal()
    try:
        patient_name = "AlertTestPatient"
        
        # Clean up any old test alerts
        db.query(HealthAlert).filter(HealthAlert.patient_name == patient_name).delete()
        db.commit()
        
        # Test 1: Critical Blood Pressure (Hypertensive Crisis)
        # Systolic 190, Diastolic 130 -> should trigger crisis alert
        print("Logging vitals: BP 190/130")
        alerts = check_and_trigger_alerts(
            db=db,
            patient_name=patient_name,
            heart_rate=88,
            blood_pressure="190/130",
            fasting_blood_sugar=95.0,
            postprandial_blood_sugar=140.0
        )
        print("Alerts triggered:", alerts)
        assert len(alerts) == 1
        assert "Hypertensive Crisis" in alerts[0]
        
        # Test 2: Hyperglycemia (Fasting blood sugar 150)
        # Fasting sugar 150 -> should trigger hyperglycemia warning
        print("\nLogging vitals: Fasting Blood Sugar 150")
        alerts2 = check_and_trigger_alerts(
            db=db,
            patient_name=patient_name,
            heart_rate=75,
            blood_pressure="120/80",
            fasting_blood_sugar=150.0,
            postprandial_blood_sugar=130.0
        )
        print("Alerts triggered:", alerts2)
        assert len(alerts2) == 1
        assert "Hyperglycemia" in alerts2[0]
        
        # Verify db persistence
        db_alerts = db.query(HealthAlert).filter(HealthAlert.patient_name == patient_name).all()
        print(f"\nSuccessfully stored {len(db_alerts)} alert records in PostgreSQL:")
        for idx, item in enumerate(db_alerts):
            print(f"{idx+1}. Type: {item.vital_type}, Level: {item.risk_level}, Message: {item.message}")
            
        assert len(db_alerts) == 2
        print("\nAll real-time alert verification tests passed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    test_alerts()
