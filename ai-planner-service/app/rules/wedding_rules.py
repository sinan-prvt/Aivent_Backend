def wedding_service_rules(budget_range: str, service: str):
    if budget_range == "under_3_lakhs":
        if service.lower() == "dj":
            return {
                "recommended": False,
                "reason": "Budget constraint"
            }

        if service.lower() == "catering":
            return {
                "recommended": True,
                "reason": "Essential service"
            }

    return None
