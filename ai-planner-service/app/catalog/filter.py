def filter_products_by_budget(products: list[dict], policy: dict) -> list[dict]:
    if not policy:
        return products

    filtered = []

    for product in products:
        try:
            price = float(product.get("price", 0))
            product["price"] = price
        except (TypeError, ValueError):
            continue

        if "max_price_per_plate" in policy:
            if price <= policy["max_price_per_plate"]:
                filtered.append(product)

        elif "max_package_price" in policy:
            if price <= policy["max_package_price"]:
                filtered.append(product)

    return filtered
