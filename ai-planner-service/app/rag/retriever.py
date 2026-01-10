from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from app.rag.knowledge import get_documents
from app.rag.catalog_loader import load_catalog_documents

_vectorstore = None

def get_retriever():
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore.as_retriever()

    docs = []
    docs.extend(get_documents())
    docs.extend(load_catalog_documents())

    if not docs:
        raise RuntimeError("No documents available for retrieval")

    try:
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://host.docker.internal:11434"
        )

        _vectorstore = FAISS.from_documents(docs, embeddings)

    except Exception as e:
        print("[AI PLANNER ERROR] Vectorstore init failed:", e)
        raise

    return _vectorstore.as_retriever()
