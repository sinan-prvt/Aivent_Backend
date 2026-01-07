import requests
from app.catalog.service_map import SERVICE_TO_CATEGORY

CATALOG_BASE = "http://catalog-service:8003/api/catalog"

def fetch_products(service: str) -> list:
    category_slug = SERVICE_TO_CATEGORY.get(service)

    if not category_slug:
        return []

    url = f"{CATALOG_BASE}/categories/{category_slug}/products/"

    try:
        res = requests.get(url, timeout=3)
        res.raise_for_status()

        data = res.json()

        # ✅ HANDLE DRF PAGINATION
        if isinstance(data, dict) and "results" in data:
            return data["results"]

        # fallback (non-paginated)
        if isinstance(data, list):
            return data

        return []

    except Exception as e:
        print("[PLANNER] Catalog fetch failed:", e, flush=True)
        return []
