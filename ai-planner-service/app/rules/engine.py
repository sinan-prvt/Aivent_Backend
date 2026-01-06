def rule_matches(rule_conditions: dict, context: dict) -> bool:
    for key, value in rule_conditions.items():
        if context.get(key) != value:
            return False
    return True


def evaluate_rules(rules: list[dict], context: dict) -> dict | None:
    sorted_rules = sorted(
        rules,
        key=lambda r: r.get("priority", 0),
        reverse=True
    )

    for rule in sorted_rules:
        if rule_matches(rule["conditions"], context):
            return rule["decision"]

    return None
