import requests
from pydantic import BaseModel
from app.catalog.service_map import SERVICE_TO_CATEGORY

class ProductDTO(BaseModel):
    id: int
    name: str
    price: float
    vendor_id: int
    category: int
    city: str = "Mumbai"
    is_available: bool = True
    stock: int = 1

CATALOG_BASE = "http://catalog-service:8000/api/catalog"

def fetch_products(service: str) -> list:
    category_slug = SERVICE_TO_CATEGORY.get(service)

    if not category_slug:
        return []

    url = f"{CATALOG_BASE}/categories/{category_slug}/products/"

    try:
        print(f"[PLANNER] Fetching products from: {url}", flush=True)
        res = requests.get(url, timeout=3)
        print(f"[PLANNER] Status: {res.status_code}", flush=True)
        
        res.raise_for_status()

        data = res.json()
        print(f"[PLANNER] Raw Response Data: {data}", flush=True)

        # ✅ HANDLE DRF PAGINATION
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            print(f"[PLANNER] Extracted {len(results)} products from pagination", flush=True)
            return [ProductDTO(**p).dict() for p in results]

        # fallback (non-paginated)
        if isinstance(data, list):
            print(f"[PLANNER] Extracted {len(data)} products from list", flush=True)
            return [ProductDTO(**p).dict() for p in data]

        print("[PLANNER] Unexpected response structure", flush=True)
        return []

    except Exception as e:
        print("[PLANNER] Catalog fetch failed:", e, flush=True)
        return []
