from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.retriever import get_retriever
from app.rules.loader import load_rules
from app.rules.engine import evaluate_rules
from app.catalog.client import fetch_products
from app.rules.budget_policy import BUDGET_POLICIES
from app.catalog.filter import filter_products_by_budget
from app.rules.services import PLANNABLE_SERVICES
from app.rules.budget_amounts import BUDGET_TOTALS
from app.rules.budget_distribution import BUDGET_DISTRIBUTION
from app.rules.budget_calculator import calculate_budget_breakdown
from app.llm.explainer import explain_service
from app.catalog.ranker import rank_products
from app.explanations.templates import RULE_BASED_EXPLANATIONS

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class UserPreferences(BaseModel):
    priority: str = "balanced"  # "price", "quality", or "balanced"
    city: str | None = None


class PlanRequest(BaseModel):
    question: str
    preferences: UserPreferences | None = None


def extract_service_from_question(question: str) -> str | None:
    q = question.lower()
    services = ["dj", "catering", "photography", "decoration", "venue", "live band", "lighting"]

    for s in services:
        if s in q:
            return s
    return None


def extract_context(question: str):
    q = question.lower()

    event_type = None
    if "wedding" in q:
        event_type = "wedding"

    budget = None
    if "under 3" in q or "3 lakh" in q:
        budget = "under_3_lakhs"

    service = extract_service_from_question(q)

    # City detection
    city = None
    cities = ["mumbai", "delhi", "bangalore", "pune", "hyderabad", "chennai", "kolkata"]
    for c in cities:
        if c in q:
            city = c.capitalize()
            break

    return {
        "event_type": event_type,
        "budget": budget,
        "service": service,
        "city": city
    }

def extract_plan_context(question: str):
    q = question.lower()

    event_type = None
    if "wedding" in q:
        event_type = "wedding"

    budget = None
    if "under 3" in q or "3 lakh" in q:
        budget = "under_3_lakhs"

    # City detection
    city = None
    cities = ["mumbai", "delhi", "bangalore", "pune", "hyderabad", "chennai", "kolkata"]
    for c in cities:
        if c in q:
            city = c.capitalize()
            break

    return {
        "event_type": event_type,
        "budget": budget,
        "city": city
    }


@router.post("/ask")
def ask(payload: PlanRequest):
    context = extract_context(payload.question)
    priority = payload.preferences.priority if payload.preferences else "balanced"
    priority_city = payload.preferences.city if payload.preferences else None

    if not context["event_type"]:
        return {"error": "Event type not identified"}

    if not context["budget"]:
        return {"error": "Budget not identified"}

    if not context["service"]:
        return {"error": "Service not identified"}

    # 🔒 RULE ENGINE FIRST (MANDATORY)
    rules = load_rules(context["event_type"])

    if not rules:
        return {
            "error": "No rules defined for this event type",
            "event_type": context["event_type"],
        }

    decision = evaluate_rules(
        rules,
        {
            "budget": context["budget"],
            "service": context["service"],
        },
    )

    if decision is not None:
        products = []

        if decision["recommended"]:
            products = fetch_products(context["service"])

            # 1. Availability/Stock Filter (Mandatory)
            products = [
                p for p in products 
                if p.get("is_available", True) and p.get("stock", 0) > 0
            ]

            # 2. City Filter
            # Priority: Preferences > Detected from context
            target_city = priority_city or context.get("city")
            if target_city:
                products = [
                    p for p in products 
                    if p.get("city", "").lower() == target_city.lower()
                ]

            policy = (
                BUDGET_POLICIES
                .get(context["budget"], {})
                .get(context["service"])
            )

            products = filter_products_by_budget(products, policy)

            if products:
                limit = (
                    policy.get("max_price_per_plate")
                    or policy.get("max_package_price")
                )
                if limit:
                    products = rank_products(products, limit, priority)

        return {
            "service": context["service"],
            "recommended": decision["recommended"],
            "reason": decision["reason"],
            "products": products,
        }

    # ⚠️ FALLBACK → INFORMATION ONLY (NO DECISIONS)
    retriever = get_retriever()
    docs = retriever.invoke(payload.question)

    return {
        "answer": "No strict rule matched. Showing general guidance only.",
        "context": docs[0].page_content if docs else None,
    }




@router.post("/plan")
def plan(payload: PlanRequest, explain: bool = False):
    context = extract_plan_context(payload.question)
    priority = payload.preferences.priority if payload.preferences else "balanced"
    priority_city = payload.preferences.city if payload.preferences else None

    if not context["event_type"] or not context["budget"]:
        return {"error": "Event type or budget not identified"}

    rules = load_rules(context["event_type"])
    if not rules:
        return {"error": "No rules defined for this event type"}

    plan = []

    # 1️⃣ BUILD PLAN
    for service in PLANNABLE_SERVICES:
        decision = evaluate_rules(
            rules,
            {
                "budget": context["budget"],
                "service": service,
            }
        )

        if decision is None:
            continue

        products = []
        if decision["recommended"]:
            products = fetch_products(service)
            print(f"[DEBUG] Raw products for {service}:", products)

            # 1. Availability/Stock Filter (Mandatory)
            products = [
                p for p in products 
                if p.get("is_available", True) and p.get("stock", 0) > 0
            ]

            # 2. City Filter
            target_city = priority_city or context.get("city")
            if target_city:
                products = [
                    p for p in products 
                    if p.get("city", "").lower() == target_city.lower()
                ]

            policy = (
                BUDGET_POLICIES
                .get(context["budget"], {})
                .get(service)
            )

            products = filter_products_by_budget(products, policy)

            if policy:
                limit = (
                    policy.get("max_price_per_plate")
                    or policy.get("max_package_price")
                )

                if limit:
                    products = rank_products(products, limit, priority)

        best_product = products[0] if products else None
        alternatives = products[1:3] if len(products) > 1 else []

        plan.append({
            "service": service,
            "recommended": decision["recommended"],
            "reason": decision["reason"],
            "recommended_product": best_product,
            "alternatives": alternatives,
        })
    # 2️⃣ CALCULATE BUDGET
    recommended_services = [
        item["service"]
        for item in plan
        if item["recommended"]
    ]

    total_budget = BUDGET_TOTALS.get(context["budget"])

    distribution = (
        BUDGET_DISTRIBUTION
        .get(context["event_type"], {})
        .get(context["budget"], {})
    )

    budget_breakdown = calculate_budget_breakdown(
        total_budget=total_budget,
        distribution=distribution,
        recommended_services=recommended_services,
    )

    # 3️⃣ BUILD RESPONSE
    response = {
        "event_type": context["event_type"],
        "budget": context["budget"],
        "budget_total": total_budget,
        "budget_breakdown": budget_breakdown,
        "plan": plan,
    }

    # 4️⃣ OPTIONAL EXPLANATION
    if explain:
        explanations = {}

        for item in plan:
            try:
                service = item["service"]
                recommended = item["recommended"]

                explanations[service] = (
                    RULE_BASED_EXPLANATIONS
                    .get(service, {})
                    .get(recommended, "No explanation available.")
                )
            except Exception:
                explanations[item["service"]] = "Explanation unavailable."

        response["explanation"] = explanations

    return response
