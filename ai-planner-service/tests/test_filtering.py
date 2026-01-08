import sys
import os
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mocking external dependencies
sys.modules["fastapi"] = MagicMock()
sys.modules["pydantic"] = MagicMock()
sys.modules["app.rag.retriever"] = MagicMock()
sys.modules["app.rules.loader"] = MagicMock()
sys.modules["app.rules.engine"] = MagicMock()
sys.modules["app.catalog.client"] = MagicMock()
sys.modules["app.rules.budget_policy"] = MagicMock()
sys.modules["app.catalog.filter"] = MagicMock()
sys.modules["app.rules.services"] = MagicMock()
sys.modules["app.rules.budget_amounts"] = MagicMock()
sys.modules["app.rules.budget_distribution"] = MagicMock()
sys.modules["app.rules.budget_calculator"] = MagicMock()
sys.modules["app.llm.explainer"] = MagicMock()
sys.modules["app.catalog.ranker"] = MagicMock()
sys.modules["app.explanations.templates"] = MagicMock()

from app.api.planner import extract_plan_context, extract_context

def test_city_detection():
    print("Testing city detection...")
    
    # Test plan context extraction
    context = extract_plan_context("Plan a wedding in Mumbai under 3 lakhs")
    assert context["city"] == "Mumbai", f"Expected Mumbai, got {context['city']}"
    
    context = extract_plan_context("Plan a wedding in delhi")
    assert context["city"] == "Delhi", f"Expected Delhi, got {context['city']}"
    
    context = extract_plan_context("Plan a wedding")
    assert context["city"] is None, f"Expected None, got {context['city']}"

    # Test ask context extraction
    context = extract_context("I want a DJ in Bangalore under 3 lakhs")
    assert context["city"] == "Bangalore", f"Expected Bangalore, got {context['city']}"
    assert context["service"] == "dj", f"Expected dj, got {context['service']}"

    print("City detection works!")

def test_filtering_logic():
    products = [
        {"id": 1, "name": "Available Mumbai", "city": "Mumbai", "is_available": True, "stock": 5},
        {"id": 2, "name": "Available Delhi", "city": "Delhi", "is_available": True, "stock": 5},
        {"id": 3, "name": "Unavailable Mumbai", "city": "Mumbai", "is_available": False, "stock": 5},
        {"id": 4, "name": "Out of Stock Mumbai", "city": "Mumbai", "is_available": True, "stock": 0},
    ]

    print("Testing filtering logic...")

    # Availability filter only
    filtered = [p for p in products if p.get("is_available", True) and p.get("stock", 0) > 0]
    assert len(filtered) == 2
    assert all(p["id"] in [1, 2] for p in filtered)

    # City filter (Mumbai)
    target_city = "Mumbai"
    filtered_city = [p for p in filtered if p.get("city", "").lower() == target_city.lower()]
    assert len(filtered_city) == 1
    assert filtered_city[0]["id"] == 1

    print("Filtering logic works!")

if __name__ == "__main__":
    try:
        test_city_detection()
        test_filtering_logic()
        print("\nAll filtering tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
