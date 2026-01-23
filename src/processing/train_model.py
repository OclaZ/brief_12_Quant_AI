# train_model.py
from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
import os
import sys
import logging

def main():
    spark = SparkSession.builder.appName("BTC-LinearRegression").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    logging.getLogger("py4j").setLevel(logging.ERROR)

    try:
        # --- PATHS ---
        input_path = "/opt/airflow/data/silver/btc_features"
        output_model_path = "/opt/airflow/models/pyspark_lr_model"

        if not os.path.exists(input_path):
            raise Exception(f"Le dossier source n'existe pas : {input_path}")

        # --- READ DATA ---
        df_spark = spark.read.parquet(input_path)

        # --- FEATURES ---
        features_keep = [
            "return_1m","ma_5","ma_10",
            "volume","close_prev","number_of_trades","taker_ratio"
        ]

        # --- CLEAN & ORDER BY TIME ---
        df_clean = df_spark.filter(F.col("close_t_plus_10").isNotNull()).orderBy("open_time")

        # --- INDEX & SPLIT ---
        w = Window.orderBy("open_time")
        df_idx = df_clean.withColumn("row_id", F.row_number().over(w))

        cutoff = int(df_idx.count() * 0.8)
        train_raw = df_idx.filter(F.col("row_id") <= cutoff)
        test_raw  = df_idx.filter(F.col("row_id") > cutoff)

        # --- VECTOR ASSEMBLER ---
        assembler = VectorAssembler(inputCols=features_keep, outputCol="features")
        train_data = assembler.transform(train_raw).select("features", "close_t_plus_10")
        test_data  = assembler.transform(test_raw).select("features", "close_t_plus_10")

        # --- LINEAR REGRESSION ---
        lr = LinearRegression(featuresCol="features", labelCol="close_t_plus_10")
        lr_model = lr.fit(train_data)

        # --- PREDICTIONS & EVALUATION ---
        predictions = lr_model.transform(test_data)
        for metric in ["rmse", "mae", "r2"]:
            score = RegressionEvaluator(
                labelCol="close_t_plus_10",
                predictionCol="prediction",
                metricName=metric
            ).evaluate(predictions)
            print(f"{metric.upper()} du Regression Linear : {score}")

        # --- SAVE MODEL ---
        os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
        lr_model.write().overwrite().save(output_model_path)
        print(f"Modèle sauvegardé dans : {output_model_path}")

    except Exception as e:
        print(f"ERREUR CRITIQUE : {e}")
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
