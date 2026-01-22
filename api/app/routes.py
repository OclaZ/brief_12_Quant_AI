from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import database, models, schemas, auth
from .config import settings
from .ml_engine import MLEngine

router = APIRouter()

# Initialisation unique du moteur ML
ml_engine = MLEngine(settings.MODEL_PATH, settings.FEATURES_COLS)

# --- AUTH ROUTES ---
@router.post("/signup", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- PREDICTION ROUTE ---
@router.post("/predict/manual", response_model=schemas.PredictionResponse)
def manual_prediction(
    market_data: schemas.MarketInput, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    try:
        # 1. Prédiction via le moteur dédié
        # On transforme l'objet Pydantic en dict pour le moteur
        prediction_value = ml_engine.predict(market_data.dict())

        # 2. Sauvegarde DB
        db_pred = models.Prediction(
            market_time=market_data.timestamp,
            predicted_price=float(prediction_value)
        )
        db.add(db_pred)
        db.commit()
        db.refresh(db_pred)
        
        return db_pred

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal ML Error")