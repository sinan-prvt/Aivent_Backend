import json
import re
from langchain_ollama import ChatOllama
from app.rules.services import PLANNABLE_SERVICES

llm = ChatOllama(
    model="qwen:0.5b",
    base_url="http://host.docker.internal:11434",
    temperature=0.1,
)

def extract_json(text: str) -> dict:
    """
    Robustly extract JSON from LLM response.
    """
    try:
        # Try finding JSON block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except:
        return None

def get_budget_distribution(event_type: str, total_budget: float) -> dict:
    """
    Asks the LLM to distribute the budget across plannable services.
    """
    prompt = f"""
    You are an expert event planner. Distribute a total budget of {total_budget} INR for a {event_type}.
    
    Services to include: {", ".join(PLANNABLE_SERVICES)}
    
    Rules:
    1. The sum of percentages must be exactly 100.
    2. Respond ONLY with a JSON object where keys are service names and values are percentages (0-100).
    3. Be realistic based on the event type.
    
    Example: {{"catering": 40, "venue": 30, ...}}
    """
    
    try:
        print(f"[LLM] Requesting budget distribution for {event_type}...", flush=True)
        response = llm.invoke(prompt)
        content = response.content.strip()
        print(f"[LLM] Raw distribution response: {content}", flush=True)
        
        distribution = extract_json(content)
        if not distribution:
             raise ValueError("Could not parse JSON from LLM response")

        # Ensure all services are present
        for s in PLANNABLE_SERVICES:
            if s not in distribution:
                distribution[s] = 0
        return distribution
    except Exception as e:
        print(f"[LLM ERROR] Budget distribution failed: {e}", flush=True)
        # Fallback to empty/default if LLM fails
        return {s: 100/len(PLANNABLE_SERVICES) for s in PLANNABLE_SERVICES}

def select_best_product(event_type: str, total_budget: float, guests: int, category: str, category_budget: float, products: list) -> dict:
    """
    Asks the LLM to select the single best product from a list.
    """
    if not products:
        print(f"[LLM] No products to select from for {category}", flush=True)
        return None
        
    # Limit product info sent to LLM to avoid token overflow
    product_summaries = [
        {"id": p['id'], "name": p['name'], "price": p['price'], "city": p.get('city', 'N/A')}
        for p in products[:5]  # Top 5 only
    ]
    
    prompt = f"""
    You are an expert event planner for a {event_type} with {guests} guests and a total budget of {total_budget} INR.
    The budget allocated for the category '{category}' is {category_budget} INR.
    
    Available Products:
    {json.dumps(product_summaries)}
    
    Instructions:
    1. Select the SINGLE BEST product that fits within the category budget of {category_budget} INR.
    2. Provide a short reason (max 15 words) why this is the best choice (e.g. style, value, or fit).
    3. Respond ONLY with a JSON object: {{"product_id": <id>, "reason": "<reason>"}}
    
    If none fit, pick the most affordable one.
    """
    
    try:
        print(f"[LLM] Requesting product selection for {category}...", flush=True)
        response = llm.invoke(prompt)
        content = response.content.strip()
        print(f"[LLM] Raw selection response for {category}: {content}", flush=True)
        
        result = extract_json(content)
        if not result:
             raise ValueError("Could not parse JSON from LLM response")

        selected_id = result.get("product_id")
        reason = result.get("reason", "Highly recommended for your event.")
        
        # Find the full product object
        for p in products:
            if p['id'] == selected_id:
                print(f"[LLM] Selected product {selected_id} for {category}", flush=True)
                return {"product": p, "reason": reason}
                
        print(f"[LLM] Selected ID {selected_id} not found in product list, falling back to first", flush=True)
        # Fallback to first if LLM returned invalid ID
        return {"product": products[0], "reason": reason}
    except Exception as e:
        print(f"[LLM ERROR] Product selection failed for {category}: {e}", flush=True)
        return {"product": products[0], "reason": "Recommended based on budget and availability."}
