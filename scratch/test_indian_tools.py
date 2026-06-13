import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.indian_apis import lookup_indian_food, lookup_ayurvedic_herb, check_drug_herb_interaction, lookup_pincode_doctor

def test_tools():
    print("=== Testing lookup_indian_food ===")
    food_res = lookup_indian_food("Plain urad dal vada")
    print(food_res)
    
    print("\n=== Testing lookup_ayurvedic_herb ===")
    herb_res = lookup_ayurvedic_herb("Hypertension")
    print(herb_res)
    
    print("\n=== Testing check_drug_herb_interaction ===")
    interaction_res = check_drug_herb_interaction(["metformin", "warfarin"], ["gudmar", "turmeric"])
    print(interaction_res)
    
    print("\n=== Testing lookup_pincode_doctor ===")
    doctor_res = lookup_pincode_doctor("560034")
    print(doctor_res)

if __name__ == "__main__":
    test_tools()
