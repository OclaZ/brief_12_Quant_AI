from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    # L'heure de la donnée (ex: la bougie de 14:00)
    market_time = Column(DateTime(timezone=True))
    # Le prix prédit
    predicted_price = Column(Float)
    # Date d'exécution de l'IA
    created_at = Column(DateTime(timezone=True), server_default=func.now())