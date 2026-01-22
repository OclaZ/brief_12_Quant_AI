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

class MarketInput(BaseModel):
    timestamp: datetime = datetime.now() # Valeur par défaut si non fournie
    open: float
    high: float
    low: float
    close: float
    volume: float
    return_1m: float
    ma_5: float
    ma_10: float
    close_prev: float
    number_of_trades: float

class PredictionResponse(BaseModel):
    id: int
    market_time: datetime
    predicted_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True