import pandas as pd
from backend.utils.csv_loader import load_ayurvedic_data, load_food_data, search_medicine_data

def lookup_indian_food(food_name: str) -> dict:
    """
    Looks up nutritional facts for a given Indian food item or recipe.
    """
    if not food_name:
        return {"error": "Food name is empty."}
        
    df = load_food_data()
    q = food_name.lower().strip()
    
    # Try exact match first on final_food_name
    match = df[df["final_food_name"].str.lower() == q]
    if match.empty:
        # Try substring match on final_food_name or recipe_original
        match = df[
            df["final_food_name"].str.lower().str.contains(q, na=False) |
            df["recipe_original"].str.lower().str.contains(q, na=False)
        ]
        
    if not match.empty:
        row = match.iloc[0]
        return {
            "food_name": row.get("final_food_name", row.get("recipe_original", food_name)),
            "cuisine": row.get("Cuisine", "Indian"),
            "calories_kcal": float(row.get("Calories (kcal)", 0.0)),
            "carbohydrates_g": float(row.get("Carbohydrates (g)", 0.0)),
            "protein_g": float(row.get("Protein (g)", 0.0)),
            "fats_g": float(row.get("Fats (g)", 0.0)),
            "fibre_g": float(row.get("Fibre (g)", 0.0)),
            "sodium_mg": float(row.get("Sodium (mg)", 0.0))
        }
        
    return {"message": f"Food item '{food_name}' not found. Using generic food estimate."}

def lookup_ayurvedic_herb(herb_name_or_disease: str) -> dict:
    """
    Retrieves Ayurvedic herb information, benefits, and recommendations for a disease or herb name.
    """
    if not herb_name_or_disease:
        return {"error": "Search query is empty."}
        
    df = load_ayurvedic_data()
    q = herb_name_or_disease.lower().strip()
    
    # Check if query matches Disease
    match = df[df["Disease"].str.lower().str.contains(q, na=False)]
    if match.empty:
        # Check if query matches Ayurvedic Herbs
        match = df[df["Ayurvedic Herbs"].str.lower().str.contains(q, na=False)]
        
    # Check if any disease in the dataset is contained in the query sentence
    if match.empty:
        disease_matches = df[df["Disease"].apply(lambda x: str(x).lower() in q if pd.notna(x) else False)]
        if not disease_matches.empty:
            match = disease_matches

    # Check if any herb name in the dataset is contained in the query sentence
    if match.empty:
        herb_matches = []
        for idx, row in df.iterrows():
            herbs_str = str(row.get("Ayurvedic Herbs", "")).lower()
            herbs = [h.strip() for h in herbs_str.split(",") if h.strip()]
            for herb in herbs:
                if herb in q and len(herb) > 3:
                    herb_matches.append(row)
                    break
        if herb_matches:
            match = pd.DataFrame(herb_matches)

    if not match.empty:
        row = match.iloc[0]
        return {
            "disease": row.get("Disease", "General Wellness"),
            "ayurvedic_herbs": row.get("Ayurvedic Herbs", "Tulsi, Ashwagandha"),
            "formulation": row.get("Formulation", "Varies"),
            "doshas": row.get("Doshas", "Vata-Pitta-Kapha"),
            "diet_lifestyle_recommendations": row.get("Diet and Lifestyle Recommendations", "Maintain balanced diet."),
            "yoga_physical_therapy": row.get("Yoga & Physical Therapy", "Pranayama, Meditation"),
            "prevention": row.get("Prevention", "Healthy daily routine"),
            "patient_recommendations": row.get("Patient Recommendations", "Consult Ayurvedic practitioner.")
        }
        
    return {"message": f"No specific Ayurvedic guidance found for '{herb_name_or_disease}'."}

# Known clinical interactions between common allopathic drugs and Ayurvedic herbs
DRUG_HERB_INTERACTIONS = {
    ("metformin", "gudmar"): "Metformin combined with Gudmar (Gymnema) can cause additive blood sugar reduction, increasing the risk of hypoglycemia. Monitor blood glucose closely.",
    ("metformin", "jamun"): "Metformin combined with Jamun can cause additive blood sugar reduction. Monitor blood glucose levels closely.",
    ("metformin", "bitter melon"): "Metformin combined with Bitter Melon (Karela) can cause additive blood sugar reduction. Monitor blood glucose levels closely.",
    ("insulin", "gudmar"): "Insulin combined with Gudmar can lead to severe hypoglycemia (dangerously low blood sugar). Avoid concurrent use without dose adjustment.",
    ("insulin", "jamun"): "Insulin combined with Jamun can lead to hypoglycemia. Monitor blood sugar levels closely.",
    ("insulin", "bitter melon"): "Insulin combined with Bitter Melon (Karela) can cause severe hypoglycemia. Monitor blood sugar levels closely.",
    ("warfarin", "turmeric"): "Turmeric (Curcumin) has mild anti-coagulant properties and can enhance the blood-thinning effect of Warfarin, increasing bleeding risks.",
    ("warfarin", "ginger"): "Ginger can inhibit platelet aggregation and increase the risk of bleeding when taken with Warfarin.",
    ("aspirin", "turmeric"): "Turmeric combined with Aspirin increases the anti-platelet effect, raising the risk of bleeding or bruising.",
    ("thyroxine", "ashwagandha"): "Ashwagandha may increase thyroid hormone levels and interfere with allopathic thyroxine therapy. Thyroid levels should be monitored.",
}

def check_drug_herb_interaction(allopathic_drugs: list[str], ayurvedic_herbs: list[str]) -> list[dict]:
    """
    Checks for potential interactions between a list of allopathic drugs and Ayurvedic herbs.
    """
    findings = []
    if not allopathic_drugs or not ayurvedic_herbs:
        return findings
        
    for drug in allopathic_drugs:
        d_norm = drug.strip().lower()
        for herb in ayurvedic_herbs:
            h_norm = herb.strip().lower()
            
            # Simple check
            warning = DRUG_HERB_INTERACTIONS.get((d_norm, h_norm))
            if not warning:
                # Substring match checks
                for (d_key, h_key), msg in DRUG_HERB_INTERACTIONS.items():
                    if d_key in d_norm and h_key in h_norm:
                        warning = msg
                        break
            
            if warning:
                findings.append({
                    "allopathic_drug": drug,
                    "ayurvedic_herb": herb,
                    "severity": "Moderate to High",
                    "warning": warning
                })
                
    return findings

def lookup_pincode_doctor(pincode: str) -> list[dict]:
    """
    Returns lists of mock doctors, clinics, and hospitals located in the region of the Indian Pincode.
    """
    pincode = str(pincode).strip()
    if not pincode.isdigit() or len(pincode) != 6:
        return [{"error": "Invalid Indian Pincode. Must be a 6-digit number."}]
        
    # Mapping based on region (first 2 digits of pincode)
    prefix = pincode[:2]
    
    if prefix == "56":
        location = "Bengaluru, Karnataka"
        doctors = [
            {"name": "Dr. Ramesh Kumar", "specialty": "Cardiologist", "clinic": "Apollo Clinic", "phone": "+91 80 4912 3456", "address": "Jayanagar, Bengaluru"},
            {"name": "Dr. Sunita Rao", "specialty": "Endocrinologist (Diabetologist)", "clinic": "Fortis Hospital", "phone": "+91 80 6199 7788", "address": "Bannerghatta Road, Bengaluru"},
            {"name": "Vaidya Ananth Shastri", "specialty": "Ayurveda Physician", "clinic": "Sri Sri Tattva Panchakarma", "phone": "+91 80 2608 0200", "address": "Kanakapura Road, Bengaluru"}
        ]
    elif prefix == "11":
        location = "New Delhi, Delhi"
        doctors = [
            {"name": "Dr. Anil Sharma", "specialty": "General Physician", "clinic": "Max Super Speciality Hospital", "phone": "+91 11 2651 5050", "address": "Saket, New Delhi"},
            {"name": "Dr. Meera Sen", "specialty": "Cardiologist", "clinic": "Medanta Medicine Clinic", "phone": "+91 11 4122 2333", "address": "Defence Colony, New Delhi"},
            {"name": "Vaidya Harish Triguna", "specialty": "Ayurveda Specialist", "clinic": "Triguna Ayurvedic Clinic", "phone": "+91 11 2689 1010", "address": "Sarita Vihar, New Delhi"}
        ]
    elif prefix == "40":
        location = "Mumbai, Maharashtra"
        doctors = [
            {"name": "Dr. Vijay Patil", "specialty": "Diabetologist", "clinic": "Lilavati Hospital", "phone": "+91 22 2675 1000", "address": "Bandra West, Mumbai"},
            {"name": "Dr. Priya Mehta", "specialty": "General Physician", "clinic": "Kokilaben Dhirubhai Ambani Hospital", "phone": "+91 22 3066 6666", "address": "Andheri West, Mumbai"},
            {"name": "Vaidya Sandeep Ranade", "specialty": "Ayurvedic Practitioner", "clinic": "Ranade Ayurveda Kendra", "phone": "+91 22 2430 4567", "address": "Dadar, Mumbai"}
        ]
    else:
        location = "General Region, India"
        doctors = [
            {"name": "Dr. Rajesh Gupta", "specialty": "General Medicine", "clinic": "Government General Hospital", "phone": "+91 98765 43210", "address": "Civil Lines"},
            {"name": "Vaidya K. P. Nair", "specialty": "Ayurveda Medicine", "clinic": "Kottakkal Arya Vaidya Sala", "phone": "+91 94470 12345", "address": "Main Road"}
        ]
        
    return {
        "pincode": pincode,
        "region_detected": location,
        "doctors": doctors
    }
