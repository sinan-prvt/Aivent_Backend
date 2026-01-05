from fastapi import APIRouter
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from app.rag.retriever import get_retriever

router = APIRouter()


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(payload: AskRequest):
    retriever = get_retriever()
    docs = retriever.invoke(payload.question)

    if not docs:
        return {"answer": "I don't have enough information to answer that."}

    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
You are an event planning assistant for AIVENT.

Rules:
- Use ONLY the information provided below.
- Do NOT invent vendors or prices.
- If information is missing, say so clearly.

Information:
{context}

User Question:
{payload.question}
"""

    llm = ChatOllama(
        model="qwen:0.5b",
        base_url="http://host.docker.internal:11434",
        temperature=0
    )

    response = llm.invoke(prompt)
    return {"answer": response.content}
