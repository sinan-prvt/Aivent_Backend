from fastapi import FastAPI
from app.api.planner import router
from app.rules.loader import load_rules


from fastapi.middleware.cors import CORSMiddleware

for event in ["wedding"]:
    load_rules(event)


app = FastAPI(title="AIVENT AI Planner Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
