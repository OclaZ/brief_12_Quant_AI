from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.types import StructType, StructField, FloatType, TimestampType
from . import database, models, schemas, auth
import os

router = APIRouter()

# --- INIT SPARK ---
print("⚡ Initialisation Spark Session...")
spark = SparkSession.builder \
    .appName("QuantAI_API") \
    .master("local[*]") \
    .config("spark.driver.memory", "1g") \
    .getOrCreate()

# --- CHARGEMENT MODELE ---
# Chemin défini par le volume Docker (ml/ -> /code/ml_store)
MODEL_PATH = "/code/ml_store/models/pyspark_rf_model"
model = None

try:
    if os.path.exists(MODEL_PATH):
        model = PipelineModel.load(MODEL_PATH)
        print(f"✅ Modèle chargé : {MODEL_PATH}")
    else:
        print(f"⚠️ Modèle introuvable à {MODEL_PATH}. L'inférence échouera.")
except Exception as e:
    print(f"⚠️ Erreur chargement modèle : {e}")

# --- ROUTES AUTH ---
@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="User exists")
    new_user = models.User(username=user.username, hashed_password=auth.get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# --- ROUTE PREDICTION (Sans Airflow) ---
@router.post("/predict/manual", response_model=schemas.PredictionResponse)
def manual_prediction(
    market_data: schemas.MarketInput, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Reçoit une bougie (Open, High, Low...) et demande au modèle Spark de prédire.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Modèle IA non chargé.")

    # 1. Créer le DataFrame Spark (Comme s'il venait de fichiers Parquet)
    # Schema Spark doit matcher les entrées
    schema = StructType([
        StructField("open", FloatType(), True),
        StructField("high", FloatType(), True),
        StructField("low", FloatType(), True),
        StructField("close", FloatType(), True),
        StructField("volume", FloatType(), True),
        # Note: Si le modèle a besoin du timestamp, il faut le gérer ici
    ])

    data = [(
        market_data.open, 
        market_data.high, 
        market_data.low, 
        market_data.close, 
        market_data.volume
    )]
    
    df = spark.createDataFrame(data, schema)

    try:
        # 2. Inférence
        predictions = model.transform(df)
        
        # 3. Extraction du résultat (supposons colonne 'prediction')
        result = predictions.select("prediction").first()
        predicted_val = result["prediction"]

        # 4. Sauvegarde
        db_pred = models.Prediction(
            market_time=market_data.timestamp,
            predicted_price=predicted_val
        )
        db.add(db_pred)
        db.commit()
        db.refresh(db_pred)
        
        return db_pred

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Spark: {str(e)}")