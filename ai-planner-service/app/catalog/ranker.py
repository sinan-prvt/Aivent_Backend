def rank_products(products: list, budget_limit: int) -> list:
    """
    Deterministic ranking:
    - cheaper products rank higher
    - products close to budget_limit get 'Best Value'
    """

    if not products:
        return []

    # sort by price (ascending)
    sorted_products = sorted(products, key=lambda p: p["price"])

    ranked = []

    for idx, product in enumerate(sorted_products, start=1):
        price = product["price"]

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
        })

    return ranked
