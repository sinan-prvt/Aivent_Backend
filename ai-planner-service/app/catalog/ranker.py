from app.catalog.vendor_scores import get_vendor_score


WEIGHT_PRESETS = {
    "price": {"price": 0.9, "quality": 0.1},
    "balanced": {"price": 0.6, "quality": 0.4},
    "quality": {"price": 0.2, "quality": 0.8},
}


def calculate_value_score(
    price: float,
    budget_limit: float,
    vendor_id: int,
    priority: str = "balanced"
) -> float:
    """
    Calculate combined value score (0.0 - 1.0).
    Higher score = better value.
    
    Weights are dynamic based on user priority:
    - price: 80% price, 20% quality
    - balanced: 60% price, 40% quality
    - quality: 30% price, 70% quality
    """
    weights = WEIGHT_PRESETS.get(priority, WEIGHT_PRESETS["balanced"])
    
    if budget_limit > 0:
        price_ratio = price / budget_limit
        price_score = max(0.0, min(1.0, 1.0 - price_ratio))
    else:
        price_score = 0.5
    
    reputation_score = get_vendor_score(vendor_id)
    
    return (weights["price"] * price_score) + (weights["quality"] * reputation_score)


def rank_products(products: list, budget_limit: int, priority: str = "balanced") -> list:
    """
    Deterministic ranking by VALUE, not just price.
    - Products with best value (price efficiency + reputation) rank higher
    - Respects user priority (price vs quality)
    - Tags: Budget Friendly / Best Value / Premium
    """

    if not products:
        return []

    scored = []
    for product in products:
        try:
            price = float(product.get("price", 0))
        except (TypeError, ValueError):
            price = 0.0
        
        vendor_id = product.get("vendor_id", 0)
        value_score = calculate_value_score(price, float(budget_limit), vendor_id, priority)
        
        scored.append({
            "product": product,
            "price": price,
            "value_score": value_score,
        })

    scored.sort(key=lambda x: x["value_score"], reverse=True)

    ranked = []
    for idx, item in enumerate(scored, start=1):
        price = item["price"]
        product = item["product"]

        if price <= budget_limit * 0.7:
            tag = "Budget Friendly"
        elif price <= budget_limit:
            tag = "Best Value"
        else:
            tag = "Premium"

        ranked.append({
            **product,
            "rank": idx,
            "tag": tag,
            "value_score": round(item["value_score"], 3),
        })

    return ranked

