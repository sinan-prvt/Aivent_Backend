from langchain_ollama import ChatOllama


llm = ChatOllama(
    model="qwen:0.5b",
    base_url="http://host.docker.internal:11434",
    temperature=0.1,
)


def explain_service(service: str, recommended: bool, reason: str, budget: str) -> str:
    prompt = f"""
Explain this decision in 1 short sentence.

Rules:
- Do NOT describe JSON
- Do NOT summarize multiple services
- Do NOT talk about the system
- Mention budget constraints if the service is not recommended

Service: {service}
Recommended: {recommended}
Reason: {reason}
Budget: {budget}
"""

    response = llm.invoke(prompt)
    return response.content.strip()
