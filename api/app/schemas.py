from pydantic import BaseModel ,ConfigDict
from datetime import datetime
from typing import Optional



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
    
    model_config = ConfigDict(from_attributes=True)