def calculate_budget_breakdown(
    total_budget: int,
    distribution: dict,
    recommended_services: list[str],
):
    breakdown = {}

    for service, percent in distribution.items():
        if service != "misc" and service not in recommended_services:
            continue

        amount = int((percent / 100) * total_budget)

        breakdown[service] = {
            "percent": percent,
            "amount": amount,
        }

    return breakdown
