"""
Vendor reputation scores for product ranking.
Until real ratings are available, this provides mock/default scores.
"""

VENDOR_SCORES: dict[int, float] = {
}


def get_vendor_score(vendor_id: int) -> float:
    """
    Get vendor reputation score.
    Returns default 0.5 (neutral) for unknown vendors.
    """
    return VENDOR_SCORES.get(vendor_id, 0.5)
