from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

# --- Prédiction ---

# Ce que l'utilisateur envoie pour demander une prédiction
class MarketInput(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    # Ajoute ici d'autres features si ton ML engineer en a besoin (ex: rsi: float)

class PredictionResponse(BaseModel):
    id: int
    market_time: datetime
    predicted_price: float
    created_at: datetime
    class Config:
        from_attributes = True