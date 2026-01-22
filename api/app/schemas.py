from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ... (Garde les classes UserBase, UserCreate, UserResponse, Token inchangées) ...
# Copie juste celles-ci si tu ne les as pas, sinon touche pas au début du fichier.

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- MODIFICATION MAJEURE ICI ---
class MarketInput(BaseModel):
    timestamp: datetime = datetime.now()
    # Les features exactes du modèle Linear Regression
    return_1m: float
    ma_5: float
    ma_10: float
    volume: float
    close_prev: float
    number_of_trades: float
    taker_ratio: float  # <--- Nouveau champ

class PredictionResponse(BaseModel):
    id: int
    market_time: datetime
    predicted_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True