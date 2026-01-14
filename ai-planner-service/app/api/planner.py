from fastapi import APIRouter
from pydantic import BaseModel
import re

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
from app.llm.planner_llm import get_budget_distribution, select_best_product

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class UserPreferences(BaseModel):
    priority: str = "balanced"
    city: str | None = None
    event_type: str | None = None
    budget: str | None = None
    guests: int | None = 100


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
    event_types = ["wedding", "birthday", "corporate", "conference", "party", "launch", "executive", "retreat", "award", "ceremony", "meeting", "summit", "festival"]
    for et in event_types:
        if et in q:
            event_type = et
            break

    budget_val = None
    # Look for numbers (e.g., 50000, 3 lakh)
    match = re.search(r'(\d+)\s*(lakh|k|thousand)?', q)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit == "lakh":
            budget_val = val * 100000
        elif unit == "k":
            budget_val = val * 1000
        else:
            budget_val = val

    budget_key = None
    if budget_val:
        if budget_val <= 300000:
            budget_key = "under_3_lakhs"
        elif budget_val <= 500000:
            budget_key = "under_5_lakhs"

    service = extract_service_from_question(q)

    city = None
    cities = ["mumbai", "delhi", "bangalore", "pune", "hyderabad", "chennai", "kolkata"]
    for c in cities:
        if c in q:
            city = c.capitalize()
            break

    return {
        "event_type": event_type,
        "budget": budget_key,
        "budget_val": budget_val,
        "service": service,
        "city": city
    }

def extract_plan_context(question: str):
    return extract_context(question)


@router.post("/ask")
def ask(payload: PlanRequest):
    # FULLY RESTORED RAG LOGIC FOR CHATBOT
    try:
        retriever = get_retriever()
        docs = retriever.invoke(payload.question)
        if docs:
            return {
                "answer": docs[0].page_content,
                "suggestions": ["Find a DJ", "Plan a Wedding", "Check Catering"]
            }
    except Exception as e:
        print(f"[RAG ERROR] Chatbot failed: {e}", flush=True)

    return {
        "answer": "I'm here to help you plan your event! Ask me about weddings, birthdays, or find specific services like DJs and caterers.",
        "suggestions": ["Plan a Wedding", "Find a DJ", "Decor ideas"]
    }


@router.post("/plan")
def plan(payload: PlanRequest, explain: bool = False):
    try:
        print(f"[PLANNER] Starting plan generation for: {payload.question}", flush=True)
        context = extract_plan_context(payload.question)
        print(f"[PLANNER] Extracted context: {context}", flush=True)
        
        event_type = context["event_type"] or (payload.preferences.event_type if payload.preferences else "Wedding")
        
        # Try to get budget from question, then preferences
        total_budget = context["budget_val"]
        if not total_budget and payload.preferences and payload.preferences.budget:
            try:
                total_budget = float(payload.preferences.budget)
            except ValueError:
                total_budget = BUDGET_TOTALS.get(payload.preferences.budget, 300000)
        
        if not total_budget:
            total_budget = 300000

        guests = payload.preferences.guests if payload.preferences and payload.preferences.guests else 100
        print(f"[PLANNER] Params: type={event_type}, budget={total_budget}, guests={guests}", flush=True)
        
        # 1️⃣ GET AI BUDGET CATEGORIZATION (PROMPTING PHASE)
        distribution = get_budget_distribution(event_type, total_budget)
        print(f"[PLANNER] AI distribution: {distribution}", flush=True)
        
        plan_items = []
        recommended_services = []

        # 2️⃣ FETCH AND SELECT PRODUCTS (PROMPTING PHASE)
        for raw_service, percent in distribution.items():
            service = raw_service.strip() # Strip any spaces from LLM
            if percent <= 0:
                continue
                
            category_budget = (percent / 100) * total_budget
            print(f"[PLANNER] Service '{service}': budget={category_budget}", flush=True)
            products = fetch_products(service)
            
            # Filter by stock/availability
            products = [p for p in products if p.get("is_available", True) and p.get("stock", 0) > 0]
            print(f"[PLANNER] Service '{service}': fetched {len(products)} available products", flush=True)
            
            # Filter by category budget (relaxed limit - 2x budget)
            filtered_products = [p for p in products if float(p.get("price", 0)) <= category_budget * 2.0]
            print(f"[PLANNER] Service '{service}': {len(filtered_products)} products within budget limit", flush=True)

            # If no products within budget, use ALL available products but tell LLM to be budget conscious
            target_products = filtered_products if filtered_products else products

            if target_products:
                # Use LLM to pick the best one
                print(f"[PLANNER] Requesting LLM selection for '{service}'...", flush=True)
                selection = select_best_product(
                    event_type=event_type,
                    total_budget=total_budget,
                    guests=guests,
                    category=service,
                    category_budget=category_budget,
                    products=target_products
                )
                
                if selection:
                    recommended_services.append(service)
                    plan_items.append({
                        "service": service,
                        "recommended": True,
                        "reason": selection["reason"],
                        "recommended_product": selection["product"],
                        "alternatives": [p for p in target_products if p['id'] != selection['product']['id']][:2],
                        "ai_pick": True
                    })
            else:
                print(f"[PLANNER] No suitable products found for '{service}'", flush=True)

        # 3️⃣ CALCULATE FINAL BUDGET BREAKDOWN
        budget_breakdown = {}
        for service, percent in distribution.items():
            budget_breakdown[service] = {
                "percent": percent,
                "amount": int((percent / 100) * total_budget)
            }

        print(f"[PLANNER] Plan generation complete. Items: {len(plan_items)}", flush=True)
        return {
            "event_type": event_type,
            "budget_val": total_budget,
            "guests": guests,
            "budget_breakdown": budget_breakdown,
            "plan": plan_items,
            "suggestions": ["Add Photography", "Change Venue", "Review Plan"]
        }
    except Exception as e:
        import traceback
        print(f"[PLANNER ERROR] Exception in plan endpoint: {e}", flush=True)
        traceback.print_exc()
        return {"error": "Internal server error during plan generation", "details": str(e)}
