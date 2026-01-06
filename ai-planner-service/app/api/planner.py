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


router = APIRouter()


class AskRequest(BaseModel):
    question: str


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

    return {
        "event_type": event_type,
        "budget": budget,
        "service": service,
    }

def extract_plan_context(question: str):
    q = question.lower()

    event_type = None
    if "wedding" in q:
        event_type = "wedding"

    budget = None
    if "under 3" in q or "3 lakh" in q:
        budget = "under_3_lakhs"

    return {
        "event_type": event_type,
        "budget": budget
    }


@router.post("/ask")
def ask(payload: AskRequest):
    context = extract_context(payload.question)

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

            policy = (
                BUDGET_POLICIES
                .get(context["budget"], {})
                .get(context["service"])
            )

            products = filter_products_by_budget(products, policy)

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
def plan(payload: AskRequest, explain: bool = False):
    context = extract_plan_context(payload.question)

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

            policy = (
                BUDGET_POLICIES
                .get(context["budget"], {})
                .get(service)
            )

            products = filter_products_by_budget(products, policy)

            if policy and "max" in policy:
                products = rank_products(products, policy["max"])

        plan.append({
            "service": service,
            "recommended": decision["recommended"],
            "reason": decision["reason"],
            "products": products,
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
                explanations[item["service"]] = explain_service(
                    service=item["service"],
                    recommended=item["recommended"],
                    reason=item["reason"],
                    budget=context["budget"],
                )
            except Exception:
                explanations[item["service"]] = "Explanation unavailable."

        response["explanation"] = explanations

    return response
