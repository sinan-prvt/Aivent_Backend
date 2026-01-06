from fastapi import FastAPI
from app.api.planner import router
from app.rules.loader import load_rules


for event in ["wedding"]:
    load_rules(event)


app = FastAPI(title="AIVENT AI Planner Service")

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
