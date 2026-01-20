from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .routes import router as auth_router

from . import database
from .import models

# Création automatique des tables (pour le dev uniquement)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Quant-AI API")
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Quant-AI API is running successfully."}

@app.get("/db-check")
def check_db(db: Session = Depends(database.get_db)):
    # Test simple : essayer d'ajouter ou lire un item
    return {"status": "Database connected successfully"}