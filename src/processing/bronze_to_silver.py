import pandas as pd
import os
import shutil
from pyspark.sql import SparkSession

def transform_silver():
    bronze_path = "/opt/airflow/data/bronze/btc_bronze.parquet"
    silver_path = "/opt/airflow/data/silver/btc_silver"
    
    spark = SparkSession.builder.appName("silver_layer").getOrCreate()
    
    # 1. Lecture et Transformation Spark
    df_spark = spark.read.parquet(bronze_path)
    df_clean = (
        df_spark
        .orderBy("open_time")
        .dropDuplicates(["open_time"])
        .dropna()
    )

    # 2. Conversion en Pandas
    df_pd = df_clean.toPandas()
    
    # 3. GESTION DU CHEMIN (Le correctif ici)
    # Si 'btc_silver' existe en tant que dossier (créé par vos essais précédents), on le supprime
    if os.path.exists(silver_path):
        if os.path.isdir(silver_path):
            shutil.rmtree(silver_path)
        else:
            os.remove(silver_path)

    # On s'assure que le dossier parent existe
    os.makedirs(os.path.dirname(silver_path), exist_ok=True)
    
    # 4. Écriture en tant que FICHIER unique
    df_pd.to_parquet(silver_path, index=False)

    spark.stop()
    return "Silver layer created successfully as a file"