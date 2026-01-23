import sys
import os
sys.path.append(os.path.join(os.environ.get("AIRFLOW_HOME", "/opt/airflow"), "src"))

from airflow.decorators import dag, task
from datetime import datetime, timedelta

from src.ingestion.binance_ingestion import data_collection_api
from src.processing.bronze_to_silver import transform_silver
from src.processing.silver_to_features import compute_silver_features
from src.processing.train_model import main
from src.processing.save_to_postgres import save_to_postgres_task

DEFAULT_ARGS = {
    "owner": "quant-ai",
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}

@dag(
    dag_id="btc_bronze_silver_features_pipeline",
    description="BTC Binance ingestion, Bronze → Silver → Features",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 1, 23),
    schedule_interval="*/10 * * * *",
    catchup=False,
    tags=["crypto", "spark", "btc"],
)
def btc_pipeline():

    # --- Ingestion Binance → Bronze
    @task
    def bronze_task():
        return data_collection_api()

    # --- Bronze → Silver
    @task
    def bronze_to_silver_task():
        return transform_silver()  # Aucun paramètre nécessaire

    # --- Silver → Features
    @task
    def silver_to_features_task():
        return compute_silver_features()  # Aucun paramètre nécessaire

    
    # --- Train model
    @task
    def train_model_task():
        main()
        return "Model trained"

    # --- Orchestration
    bronze = bronze_task()
    silver = bronze_to_silver_task()
    features = silver_to_features_task()
   
    train_task = train_model_task()

    bronze >> silver >> features  >> train_task

dag = btc_pipeline()
