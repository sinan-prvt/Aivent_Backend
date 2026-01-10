"""
Tests for value-based product ranking.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.catalog.ranker import rank_products, calculate_value_score
from app.catalog import vendor_scores


def test_value_score_calculation():
    """Test that value score combines price efficiency and reputation."""
    score1 = calculate_value_score(price=100, budget_limit=1000, vendor_id=999)
    
    score2 = calculate_value_score(price=900, budget_limit=1000, vendor_id=999)
    
    assert score1 > score2, "Cheaper product should have higher value score"


def test_reputation_affects_ranking():
    """Test that high-reputation vendor can beat a cheaper but unknown vendor."""
    vendor_scores.VENDOR_SCORES[100] = 0.9
    vendor_scores.VENDOR_SCORES[200] = 0.2 
    
    products = [
        {"id": 1, "name": "Cheap Low Rep", "price": 500, "vendor_id": 200, "category": 1},
        {"id": 2, "name": "Pricier High Rep", "price": 600, "vendor_id": 100, "category": 1},
    ]
    
    ranked_balanced = rank_products(products, budget_limit=1000)
    assert ranked_balanced[0]["id"] == 2, "In balanced mode, high reputation should win"
    
    ranked_price = rank_products(products, budget_limit=1000, priority="price")
    assert ranked_price[0]["id"] == 1, "In price mode, cheaper vendor should win"
    
    ranked_quality = rank_products(products, budget_limit=1000, priority="quality")
    assert ranked_quality[0]["id"] == 2, "In quality mode, high reputation should win"
    
    del vendor_scores.VENDOR_SCORES[100]
    del vendor_scores.VENDOR_SCORES[200]


def test_deterministic_ranking():
    """Test that same input always produces same output."""
    products = [
        {"id": 1, "name": "Product A", "price": 500, "vendor_id": 1, "category": 1},
        {"id": 2, "name": "Product B", "price": 600, "vendor_id": 2, "category": 1},
        {"id": 3, "name": "Product C", "price": 400, "vendor_id": 3, "category": 1},
    ]
    
    result1 = rank_products(products, budget_limit=1000)
    result2 = rank_products(products, budget_limit=1000)
    
    assert result1 == result2, "Ranking should be deterministic"


def test_empty_products():
    """Test that empty list returns empty list."""
    assert rank_products([], budget_limit=1000) == []


def test_tags_assigned_correctly():
    """Test Budget Friendly / Best Value / Premium tags."""
    products = [
        {"id": 1, "name": "Cheap", "price": 200, "vendor_id": 1, "category": 1},  # <= 70%
        {"id": 2, "name": "Mid", "price": 800, "vendor_id": 2, "category": 1},    # <= 100%
        {"id": 3, "name": "Expensive", "price": 1500, "vendor_id": 3, "category": 1},  # > 100%
    ]
    
    ranked = rank_products(products, budget_limit=1000)
    
    tags = {p["id"]: p["tag"] for p in ranked}
    
    assert tags[1] == "Budget Friendly"
    assert tags[2] == "Best Value"
    assert tags[3] == "Premium"


if __name__ == "__main__":
    test_value_score_calculation()
    test_reputation_affects_ranking()
    test_deterministic_ranking()
    test_empty_products()
    test_tags_assigned_correctly()
    print("All ranker tests passed!")
