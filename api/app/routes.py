from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import database, models, schemas, auth

router = APIRouter()

# --- Endpoint 1 : Inscription (Sign Up) ---
@router.post("/signup", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # 1. Vérifier si l'utilisateur existe déjà
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. Hacher le mot de passe
    hashed_password = auth.get_password_hash(user.password)
    
    # 3. Sauvegarder en base
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# --- Endpoint 2 : Connexion (Login) ---
@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # 1. Chercher l'utilisateur
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # 2. Vérifier le mot de passe
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Générer le token JWT
    access_token = auth.create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}