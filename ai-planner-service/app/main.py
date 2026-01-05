from fastapi import FastAPI
from app.api.planner import router

app = FastAPI(title="AIVENT AI Planner Service")

app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}