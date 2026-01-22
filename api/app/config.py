import os

class Settings:
    # Postgres
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
    DB_SERVER = os.getenv("POSTGRES_SERVER", "postgres")
    DB_NAME = os.getenv("POSTGRES_DB", "quant_db")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"

    # ML Settings
    MODEL_PATH = "/code/ml_store/models/pyspark_lr_model"
    
    # La liste officielle des features
    FEATURES_COLS = [
        "return_1m", 
        "ma_5", 
        "ma_10",
        "volume", 
        "close_prev", 
        "number_of_trades", 
        "taker_ratio"
    ]

settings = Settings()