import os
import sys
import json
from pathlib import Path
import pandas as pd

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

AYURVEDIC_CSV = DATA_DIR / "Ayurvedic_Dataset" / "AyurGenixAI_Dataset.csv"
FOOD_CSV = DATA_DIR / "Indian_food" / "Indian_Food_Ingredients_Nutrition_CookingMethods.csv"
MEDICINE_CSV = DATA_DIR / "Indian_Medicine_Data" / "medicine_data.csv"

# Fallback Data Structures in case files are missing or corrupted
FALLBACK_FOODS = [
    {"final_food_name": "Roti", "Calories (kcal)": 120, "Carbohydrates (g)": 24.0, "Protein (g)": 3.5, "Fats (g)": 0.8},
    {"final_food_name": "Paneer Tikka Masala", "Calories (kcal)": 380, "Carbohydrates (g)": 14.0, "Protein (g)": 15.0, "Fats (g)": 28.0},
    {"final_food_name": "Moong Dal Tadka", "Calories (kcal)": 180, "Carbohydrates (g)": 25.0, "Protein (g)": 8.0, "Fats (g)": 4.5},
    {"final_food_name": "Chicken Biryani", "Calories (kcal)": 520, "Carbohydrates (g)": 55.0, "Protein (g)": 22.0, "Fats (g)": 18.0},
    {"final_food_name": "Idli with Sambar", "Calories (kcal)": 210, "Carbohydrates (g)": 38.0, "Protein (g)": 6.0, "Fats (g)": 2.0}
]

FALLBACK_HERBS = [
    {
        "Disease": "Hypertension",
        "Ayurvedic Herbs": "Ashwagandha, Arjuna",
        "Diet and Lifestyle Recommendations": "Reduce salt; practice yoga and meditation; avoid spicy foods.",
        "Yoga & Physical Therapy": "Surya Namaskar, Meditation"
    },
    {
        "Disease": "Diabetes",
        "Ayurvedic Herbs": "Jamun, Gudmar",
        "Diet and Lifestyle Recommendations": "Avoid sugary foods; focus on low-GI foods; regular exercise.",
        "Yoga & Physical Therapy": "Surya Namaskar, Pranayama"
    },
    {
        "Disease": "Cough",
        "Ayurvedic Herbs": "Tulsi, Ginger",
        "Diet and Lifestyle Recommendations": "Avoid cold foods; stay hydrated; consume warm liquids.",
        "Yoga & Physical Therapy": "Anulom Vilom, Pranayama"
    }
]

FALLBACK_MEDICINES = [
    {
        "product_name": "Human Insulatard 40IU/ml Suspension",
        "salt_composition": "Insulin Isophane (40IU)",
        "medicine_desc": "Used to improve blood sugar control in Type 1 and Type 2 diabetes.",
        "side_effects": "Hypoglycemia, injection site reaction",
        "drug_interactions": '{"drug": ["Benazepril", "Captopril"], "effect": ["MODERATE", "MODERATE"]}'
    },
    {
        "product_name": "Paracetamol 650",
        "salt_composition": "Paracetamol (650mg)",
        "medicine_desc": "Used for relieving fever and mild pain.",
        "side_effects": "Nausea, liver damage in high doses",
        "drug_interactions": '{"drug": ["Warfarin"], "effect": ["MODERATE"]}'
    }
]

def load_ayurvedic_data() -> pd.DataFrame:
    """Loads the Ayurvedic herbs and remedies dataset."""
    if AYURVEDIC_CSV.exists():
        try:
            return pd.read_csv(AYURVEDIC_CSV)
        except Exception as e:
            print(f"Error loading Ayurvedic CSV: {e}", file=sys.stderr)
    return pd.DataFrame(FALLBACK_HERBS)

def load_food_data() -> pd.DataFrame:
    """Loads the Indian food nutrition dataset."""
    if FOOD_CSV.exists():
        try:
            return pd.read_csv(FOOD_CSV)
        except Exception as e:
            print(f"Error loading Food CSV: {e}", file=sys.stderr)
    return pd.DataFrame(FALLBACK_FOODS)

def search_medicine_data(query: str, limit: int = 5) -> list[dict]:
    """
    Searches the large medicine database in chunks to optimize memory usage.
    Returns a list of dicts matching the product name or salt composition.
    """
    if not query:
        return []
    
    query = query.lower().strip()
    
    if MEDICINE_CSV.exists():
        try:
            results = []
            # Read in chunks of 20,000 rows to keep memory usage extremely low
            for chunk in pd.read_csv(MEDICINE_CSV, chunksize=20000):
                matches = chunk[
                    chunk["product_name"].str.lower().str.contains(query, na=False) |
                    chunk["salt_composition"].str.lower().str.contains(query, na=False)
                ]
                if not matches.empty:
                    results.extend(matches.to_dict(orient="records"))
                    if len(results) >= limit:
                        return results[:limit]
            if results:
                return results
        except Exception as e:
            print(f"Error reading medicine CSV: {e}", file=sys.stderr)
            
    # Fallback search
    results = []
    for med in FALLBACK_MEDICINES:
        if (query in med["product_name"].lower() or 
            query in med["salt_composition"].lower()):
            results.append(med)
    return results[:limit]
