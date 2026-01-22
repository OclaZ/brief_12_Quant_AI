import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Imports PySpark
from pyspark.sql import SparkSession
# ON IMPORTE UNIQUEMENT CE DONT ON A BESOIN
from pyspark.ml.regression import RandomForestRegressionModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.types import StructType, StructField, FloatType

# Imports internes
from . import database, models, schemas, auth

router = APIRouter()

# ----------------------------------------------------------------
# 1. INITIALISATION SPARK
# ----------------------------------------------------------------
print("Initialisation de la session Spark...")
spark = SparkSession.builder \
    .appName("QuantAI_API") \
    .master("local[*]") \
    .config("spark.driver.memory", "1g") \
    .getOrCreate()

print(f"ℹ️ Version de Spark utilisée par l'API : {spark.version}")

# ----------------------------------------------------------------
# 2. CHARGEMENT CIBLÉ DU MODÈLE (Random Forest)
# ----------------------------------------------------------------
MODEL_PATH = "/code/ml_store/models/pyspark_rf_model"
model = None

if os.path.exists(MODEL_PATH):
    print(f"Dossier modèle trouvé : {MODEL_PATH}")
    try:
        # ON FORCE LE CHARGEMENT EN RANDOM FOREST
        model = RandomForestRegressionModel.load(MODEL_PATH)
        print("✅ Modèle Random Forest chargé avec succès !")
    except Exception as e:
        print(f"❌ Erreur critique lors du chargement du modèle : {e}")
        # On affiche l'erreur complète pour comprendre pourquoi ça bloque
        import traceback
        traceback.print_exc()
        model = None
else:
    print(f"⚠️ Aucun modèle trouvé à l'emplacement : {MODEL_PATH}")

# ----------------------------------------------------------------
# 3. ROUTES D'AUTHENTIFICATION (Inchangées)
# ----------------------------------------------------------------
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

# ----------------------------------------------------------------
# 4. ROUTE DE PRÉDICTION
# ----------------------------------------------------------------
@router.post("/predict/manual", response_model=schemas.PredictionResponse)
def manual_prediction(
    market_data: schemas.MarketInput, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not model:
        raise HTTPException(status_code=503, detail="Modèle IA non chargé. Vérifiez les logs du serveur.")

    # A. Features exactes
    features_cols = [
        "open", "high", "low", "close",
        "return_1m", "ma_5", "ma_10",
        "volume", "close_prev", "number_of_trades"
    ]

    # B. Création DataFrame
    schema = StructType([StructField(col, FloatType(), True) for col in features_cols])
    data_tuple = (
        market_data.open, market_data.high, market_data.low, market_data.close,
        market_data.return_1m, market_data.ma_5, market_data.ma_10,
        market_data.volume, market_data.close_prev, market_data.number_of_trades
    )
    df = spark.createDataFrame([data_tuple], schema)

    try:
        # C. Assemblage des Features (Car ce n'est pas un Pipeline)
        assembler = VectorAssembler(inputCols=features_cols, outputCol="features")
        df_assembled = assembler.transform(df)

        # D. Prédiction
        predictions = model.transform(df_assembled)
        
        # E. Récupération Résultat
        if 'prediction' in predictions.columns:
            val = predictions.select("prediction").first()["prediction"]
        else:
            val = 0.0

        # F. Sauvegarde DB
        db_pred = models.Prediction(
            market_time=market_data.timestamp,
            predicted_price=float(val)
        )
        db.add(db_pred)
        db.commit()
        db.refresh(db_pred)
        
        return db_pred

    except Exception as e:
        print(f"❌ Erreur Prédiction : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur Spark: {str(e)}")