from fastapi import FastAPI
from . import models, database
from .routes import router as api_router

# Création tables DB
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Quant-AI Backend")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health():
    return {"status": "ok", "mode": "No-Airflow / Real-time Inference"}