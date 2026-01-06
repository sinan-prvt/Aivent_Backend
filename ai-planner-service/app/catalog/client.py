import requests
from app.catalog.service_map import SERVICE_TO_CATEGORY

CATALOG_BASE = "http://catalog-service:8000/api/catalog"

def fetch_products(service: str) -> list:
    category_slug = SERVICE_TO_CATEGORY.get(service)

    print(f"[PLANNER DEBUG] service={service}, slug={category_slug}", flush=True)

    if not category_slug:
        return []

    url = f"{CATALOG_BASE}/categories/{category_slug}/products/"
    print(f"[PLANNER DEBUG] calling URL: {url}", flush=True)

    try:
        res = requests.get(url, timeout=3)
        print(f"[PLANNER DEBUG] status={res.status_code}", flush=True)
        print(f"[PLANNER DEBUG] body={res.text[:300]}", flush=True)

        res.raise_for_status()
        return res.json()

    except Exception as e:
        print("[PLANNER] Catalog fetch failed:", e, flush=True)
        return []
