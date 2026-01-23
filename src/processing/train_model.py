# /opt/airflow/src/processing/train_model.py
import pandas as pd
import os
import sys
import logging
from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator

def main():
    # Initialisation Spark avec options de compatibilité Parquet
    spark = SparkSession.builder \
        .appName("BTC-LinearRegression") \
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED") \
        .config("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")
    logging.getLogger("py4j").setLevel(logging.ERROR)

    try:
        # --- PATHS ---
        input_path = "/opt/airflow/data/silver/btc_features"
        output_model_path = "/opt/airflow/models/pyspark_lr_model"

        if not os.path.exists(input_path):
            raise Exception(f"Le dossier source n'existe pas : {input_path}")

        # --- READ DATA (Fix Pandas 1.x Compatibility) ---
        print(f"Lecture des données via Pandas : {input_path}")
        pdf = pd.read_parquet(input_path)
        
        # Correction robuste : on cherche 'datetime' au sens large 
        # Cela évite l'erreur sur la fréquence [us] ou [ns]
        datetime_cols = pdf.select_dtypes(include=['datetime', 'datetimetz']).columns
        for col in datetime_cols:
            pdf[col] = pd.to_datetime(pdf[col])
            
        # Conversion vers Spark
        df_spark = spark.createDataFrame(pdf)

        # --- FEATURES ---
        features_keep = [
            "return_1m", "ma_5", "ma_10",
            "volume", "close_prev", "number_of_trades", "taker_ratio"
        ]

        # --- CLEAN & ORDER BY TIME ---
        # On force open_time en timestamp Spark pour la Window function
        df_clean = df_spark.filter(F.col("close_t_plus_10").isNotNull()) \
                           .withColumn("open_time", F.col("open_time").cast("timestamp")) \
                           .orderBy("open_time")

        # --- INDEX & SPLIT ---
        w = Window.orderBy("open_time")
        df_idx = df_clean.withColumn("row_id", F.row_number().over(w))

        total_rows = df_idx.count()
        if total_rows == 0:
            raise Exception("Le DataFrame Spark est vide après conversion.")

        cutoff = int(total_rows * 0.8)
        train_raw = df_idx.filter(F.col("row_id") <= cutoff)
        test_raw  = df_idx.filter(F.col("row_id") > cutoff)

        # --- VECTOR ASSEMBLER ---
        # handleInvalid="skip" est vital si les MA (Moving Averages) ont des nulls au début
        assembler = VectorAssembler(inputCols=features_keep, outputCol="features", handleInvalid="skip")
        
        train_data = assembler.transform(train_raw).select("features", "close_t_plus_10")
        test_data  = assembler.transform(test_raw).select("features", "close_t_plus_10")

        # --- LINEAR REGRESSION ---
        print("Entraînement du modèle Linear Regression...")
        lr = LinearRegression(featuresCol="features", labelCol="close_t_plus_10")
        lr_model = lr.fit(train_data)

        # --- EVALUATION ---
        predictions = lr_model.transform(test_data)
        
        print("\n" + "="*30)
        print("METRIQUES DE VALIDATION")
        print("="*30)
        for metric in ["rmse", "mae", "r2"]:
            score = RegressionEvaluator(
                labelCol="close_t_plus_10",
                predictionCol="prediction",
                metricName=metric
            ).evaluate(predictions)
            print(f"{metric.upper()} : {score}")
        print("="*30 + "\n")

        # --- SAVE MODEL ---
        os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
        lr_model.write().overwrite().save(output_model_path)
        print(f"Modèle sauvegardé avec succès : {output_model_path}")

    except Exception as e:
        print(f"ERREUR CRITIQUE DANS TRAIN_MODEL : {e}")
        raise e 
    finally:
        spark.stop()

if __name__ == "__main__":
    main()