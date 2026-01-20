from pydantic import BaseModel
from typing import Optional

# --- Schémas Utilisateurs ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    is_active: bool
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None