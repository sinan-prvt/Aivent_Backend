"""
Vendor reputation scores for product ranking.
Until real ratings are available, this provides mock/default scores.
"""

# Default vendor scores (0.0 - 1.0)
# Higher = better reputation
VENDOR_SCORES: dict[int, float] = {
    # vendor_id: reputation_score
    # Example: 1: 0.9, 2: 0.7, etc.
}


def get_vendor_score(vendor_id: int) -> float:
    """
    Get vendor reputation score.
    Returns default 0.5 (neutral) for unknown vendors.
    """
    return VENDOR_SCORES.get(vendor_id, 0.5)
