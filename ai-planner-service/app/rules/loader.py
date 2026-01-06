import yaml
from pathlib import Path
from app.rules.schema import RuleFile

RULES_PATH = Path(__file__).parent / "data"


def load_rules(event_type: str) -> list[dict]:
    file_path = RULES_PATH / f"{event_type}.yaml"

    if not file_path.exists():
        raise RuntimeError(f"No rule file found for event_type='{event_type}'")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    try:
        validated = RuleFile(**raw)
    except Exception as e:
        raise RuntimeError(
            f"Invalid rule schema in {file_path.name}: {e}"
        )

    return [rule.model_dump() for rule in validated.rules]
