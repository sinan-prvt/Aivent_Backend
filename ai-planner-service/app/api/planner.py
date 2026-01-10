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
    priority: str = "balanced"
    city: str | None = None
    event_type: str | None = None
    budget: str | None = None


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
    elif "under 5" in q or "5 lakh" in q:
        budget = "under_5_lakhs"

    service = extract_service_from_question(q)

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
    elif "under 5" in q or "5 lakh" in q:
        budget = "under_5_lakhs"

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
        context["event_type"] = (payload.preferences.event_type if payload.preferences else None) or "wedding"

    if not context["budget"]:
        context["budget"] = (payload.preferences.budget if payload.preferences else None) or "under_3_lakhs"

    state_context = {
        "event_type": context["event_type"],
        "budget": context["budget"]
    }

    if not context["service"]:
        if context["event_type"] and context["budget"]:
            total = BUDGET_TOTALS.get(context["budget"], 0)
            dist = BUDGET_DISTRIBUTION.get(context["event_type"], {}).get(context["budget"], {})
            
            summary_parts = [f"I can help you plan your {context['event_type']} for ₹{total:,}!"]
            summary_parts.append("\nHere's a recommended budget breakdown:")
            
            for s, pct in dist.items():
                amt = (pct / 100) * total
                summary_parts.append(f"• **{s.capitalize()}**: ₹{int(amt):,}")
            
            summary_parts.append("\nWhich service should we find products for first? (e.g., 'Find a DJ')")
            
            return {
                "explanation": "\n".join(summary_parts),
                "products": [],
                "context": state_context,
                "suggestions": [f"Find {s}" for s in PLANNABLE_SERVICES[:3]]
            }

        return {
            "error": "Service not identified",
            "message": "I can help you find DJs, caterers, or decorators. What's on your mind?",
            "context": state_context,
            "suggestions": ["Plan a Wedding", "Find a DJ", "Check Catering", "Decor ideas"]
        }

    rules = load_rules(context["event_type"])

    if not rules:
        return {
            "error": "No rules defined for this event type",
            "event_type": context["event_type"],
            "suggestions": ["Try 'Wedding'", "Help me plan"]
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

            products = [
                p for p in products 
                if p.get("is_available", True) and p.get("stock", 0) > 0
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

        all_services = ["dj", "catering", "photography", "decoration", "venue"]
        suggestions = [f"Find {s}" for s in all_services if s != context["service"]]
        if not products:
            suggestions.insert(0, f"Try different {context['service']}")

        return {
            "service": context["service"],
            "recommended": decision["recommended"],
            "reason": decision["reason"],
            "products": products,
            "context": state_context,
            "suggestions": suggestions[:3]
        }

    retriever = get_retriever()
    docs = retriever.invoke(payload.question)

    return {
        "answer": "No strict rule matched. Showing general guidance only.",
        "context_info": docs[0].page_content if docs else None,
        "context": state_context,
        "suggestions": ["Find a DJ", "Catering options", "Plan a Wedding"]
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

            products = [
                p for p in products 
                if p.get("is_available", True) and p.get("stock", 0) > 0
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

    suggestions = []
    if context["budget"] == "under_3_lakhs":
        suggestions.append("Upgrade to 5 Lakhs")
    else:
        suggestions.append("Check 3 Lakhs Plan")
    suggestions.extend(["Find a DJ", "Catering details", "Photography"])

    response = {
        "event_type": context["event_type"],
        "budget": context["budget"],
        "budget_total": total_budget,
        "budget_breakdown": budget_breakdown,
        "plan": plan,
        "suggestions": suggestions[:3]
    }

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
