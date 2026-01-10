import requests
from langchain_core.documents import Document

CATALOG_SERVICE_URL = "http://catalog-service:8000/api/catalog/categories/"

def load_catalog_documents():
    documents = []

    try:
        print(f"[AI PLANNER] Fetching catalog from: {CATALOG_SERVICE_URL}", flush=True)
        response = requests.get(CATALOG_SERVICE_URL, timeout=3)
        print(f"[AI PLANNER] Status: {response.status_code}", flush=True)
        
        if response.status_code != 200:
             print(f"[AI PLANNER] Error Response: {response.text[:500]}", flush=True)

        response.raise_for_status()
        categories = response.json()
    except Exception as e:
        print(f"[AI PLANNER] Catalog unavailable: {e}")
        return documents

    for cat in categories:
        name = cat.get("name")
        if not name:
            continue

        documents.append(
    Document(
        page_content=f"""
SERVICE CATEGORY: {name}

ROLE IN EVENTS:
This service category plays an important role in event planning.
It may include professional offerings, logistics, and coordination
related to {name.lower()} services.

USAGE CONTEXT:
This category can be selected based on event type, guest count,
and available budget.
"""
    )
)

    return documents
