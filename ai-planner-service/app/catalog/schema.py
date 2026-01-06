from pydantic import BaseModel
from typing import Optional


class ProductScore(BaseModel):
    id: int
    name: str
    price: int
    vendor_id: int

    rank: int
    tag: str  # Best Value | Budget Friendly | Premium
