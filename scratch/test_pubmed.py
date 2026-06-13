import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.research_tool import search_medical_information

def test_pubmed():
    print("=== Testing PubMed Fetching & Summarization ===")
    
    # Run dynamic query
    query = "diabetes clinical guidelines"
    print(f"Searching PubMed for: '{query}'...")
    res = search_medical_information(query)
    
    print("\n--- Summary Results ---")
    print(res["summary"])
    
    bullets = res["bullets"]
    print(f"\nTotal bullet points generated: {len(bullets)}")
    
    # Assertions
    assert 5 <= len(bullets) <= 10, "Summary must contain between 5 and 10 bullet points."
    print("\nPubMed research summarization dry run test passed successfully!")

if __name__ == "__main__":
    test_pubmed()
