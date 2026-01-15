import requests
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from app.catalog.service_map import SERVICE_TO_CATEGORY

class ProductDTO(BaseModel):
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields from API
    
    id: int
    name: str
    price: float
    vendor_id: int
    category: int
    city: str = "Mumbai"
    is_available: bool = True
    stock: int = 1
    image: Optional[Any] = None  # Can be string URL or complex object

CATALOG_BASE = "http://catalog-service:8000/api/catalog"

# Cache for categories
_category_cache = None

def fetch_categories() -> dict:
    """Fetch all categories from catalog and build a name/slug mapping."""
    global _category_cache
    if _category_cache is not None:
        return _category_cache
    
    try:
        print("[PLANNER] Fetching categories from catalog...", flush=True)
        res = requests.get(f"{CATALOG_BASE}/categories/", timeout=10)
        res.raise_for_status()
        data = res.json()
        
        # Build a mapping from various name forms to slugs
        category_map = {}
        
        def process_category(cat):
            name = cat.get('name', '')
            slug = cat.get('slug', '')
            if name and slug:
                # Add multiple variations for matching
                category_map[name.lower()] = slug
                category_map[slug.lower()] = slug
                # Add simplified versions (e.g., "Decoration & Styling" -> "decoration")
                simple_name = name.lower().split('&')[0].split(' ')[0].strip()
                if simple_name:
                    category_map[simple_name] = slug
            
            # Process children recursively
            for child in cat.get('children', []):
                process_category(child)
        
        if isinstance(data, list):
            for cat in data:
                process_category(cat)
        elif isinstance(data, dict) and 'results' in data:
            for cat in data['results']:
                process_category(cat)
        
        print(f"[PLANNER] Built category map: {category_map}", flush=True)
        _category_cache = category_map
        return category_map
    except Exception as e:
        print(f"[PLANNER] Failed to fetch categories: {e}", flush=True)
        return {}

def get_category_slug(service: str) -> str | None:
    """Get category slug for a service name using dynamic or static mapping."""
    # First try the hardcoded map
    slug = SERVICE_TO_CATEGORY.get(service)
    
    # Then try dynamic category map
    if not slug:
        category_map = fetch_categories()
        slug = category_map.get(service.lower())
    
    print(f"[PLANNER] Resolved service '{service}' to slug '{slug}'", flush=True)
    return slug

def fetch_products(service: str) -> list:
    category_slug = get_category_slug(service)

    if not category_slug:
        print(f"[PLANNER] No category slug found for service '{service}'", flush=True)
        return []

    url = f"{CATALOG_BASE}/categories/{category_slug}/products/"

    try:
        print(f"[PLANNER] Fetching products from: {url}", flush=True)
        res = requests.get(url, timeout=10)
        print(f"[PLANNER] Status: {res.status_code}", flush=True)
        
        if res.status_code == 404:
            print(f"[PLANNER] Category '{category_slug}' not found in catalog", flush=True)
            return []
        
        res.raise_for_status()

        data = res.json()
        print(f"[PLANNER] Raw Response Data: {data}", flush=True)

        products = []
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            print(f"[PLANNER] Extracted {len(results)} products from pagination", flush=True)
            for p in results:
                try:
                    products.append(ProductDTO(**p).model_dump())
                except Exception as e:
                    print(f"[PLANNER] Failed to parse product: {e}", flush=True)
        elif isinstance(data, list):
            print(f"[PLANNER] Extracted {len(data)} products from list", flush=True)
            for p in data:
                try:
                    products.append(ProductDTO(**p).model_dump())
                except Exception as e:
                    print(f"[PLANNER] Failed to parse product: {e}", flush=True)
        else:
            print("[PLANNER] Unexpected response structure", flush=True)
        
        return products

    except Exception as e:
        print(f"[PLANNER] Catalog fetch failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []
