from pydantic import BaseModel
from typing import List, Dict


class RuleDecision(BaseModel):
    recommended: bool
    reason: str


class Rule(BaseModel):
    id: str
    priority: int
    conditions: Dict[str, str]
    decision: RuleDecision


class RuleFile(BaseModel):
    event_type: str
    rules: List[Rule]
