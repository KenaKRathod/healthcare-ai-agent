import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ml.health_prediction import calculate_idrs

def test_idrs():
    print("=== Testing Indian Diabetes Risk Score (IDRS) ===")
    
    # Test 1: High Risk Patient
    # Age 52 (30 pts), Waist 95 cm for Male (10 pts), Sedentary (20 pts), Both parents diabetic (20 pts) -> 80 (High Risk)
    res_high = calculate_idrs(age=52, waist_cm=95, activity="sedentary", family_diabetic="both", sex="male")
    print("\nTest 1 (Expected: Score 80, High Risk):")
    print(res_high)
    assert res_high["score"] == 80
    assert res_high["risk_level"] == "high"
    
    # Test 2: Medium Risk Patient
    # Age 38 (20 pts), Waist 85 cm for Female (10 pts), Moderate (10 pts), One parent diabetic (10 pts) -> 50 (Medium Risk)
    res_med = calculate_idrs(age=38, waist_cm=85, activity="moderate", family_diabetic="one", sex="female")
    print("\nTest 2 (Expected: Score 50, Medium Risk):")
    print(res_med)
    assert res_med["score"] == 50
    assert res_med["risk_level"] == "medium"
    
    # Test 3: Low Risk Patient
    # Age 25 (0 pts), Waist 75 cm for Female (0 pts), Active (0 pts), No parent diabetic (0 pts) -> 0 (Low Risk)
    res_low = calculate_idrs(age=25, waist_cm=75, activity="active", family_diabetic="no", sex="female")
    print("\nTest 3 (Expected: Score 0, Low Risk):")
    print(res_low)
    assert res_low["score"] == 0
    assert res_low["risk_level"] == "low"
    
    print("\nAll IDRS validation tests passed successfully!")

if __name__ == "__main__":
    test_idrs()
