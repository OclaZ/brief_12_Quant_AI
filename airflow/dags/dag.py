from airflow.decorators import dag, task
from datetime import datetime

import requests
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator


# -------------------- CONSTANTS --------------------
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LIMIT = 600

BRONZE_PATH = "data/bronze/bronze.parquet"
SILVER_PATH = "data/silver/btc_silver"
FEATURES_PATH = "data/silver/btc_features"
MODEL_PATH = "models/btc_lr_model"


# -------------------- DAG --------------------
@dag(
    dag_id="btc_bronze_silver_features_training",
    start_date=datetime(2025, 1, 15),
    schedule=None,
    catchup=False,
    tags=["btc", "spark", "ml"]
)
def btc_pipeline():

    # ---------- Spark ----------
    def get_spark(app_name):
        return (
            SparkSession.builder
            .appName(app_name)
            .config("spark.driver.memory", "4g")
            .getOrCreate()
        )

    # ---------- TASK 1 : BRONZE ----------
    @task
    def collect_bronze():
        spark = get_spark("collect_bronze")

        response = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={
                "symbol": SYMBOL,
                "interval": INTERVAL,
                "limit": LIMIT
            }
        )

        if response.status_code != 200:
            raise Exception("Erreur API Binance")

        data = response.json()

        columns = [
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
        ]

        df = spark.createDataFrame(data, columns)

        df = (
            df
            .withColumn("open_time", F.to_timestamp(F.col("open_time") / 1000))
            .withColumn("close_time", F.to_timestamp(F.col("close_time") / 1000))
            .withColumn("open", F.col("open").cast("double"))
            .withColumn("high", F.col("high").cast("double"))
            .withColumn("low", F.col("low").cast("double"))
            .withColumn("close", F.col("close").cast("double"))
            .withColumn("volume", F.col("volume").cast("double"))
            .withColumn("quote_asset_volume", F.col("quote_asset_volume").cast("double"))
            .withColumn("taker_buy_base_volume", F.col("taker_buy_base_volume").cast("double"))
            .withColumn("taker_buy_quote_volume", F.col("taker_buy_quote_volume").cast("double"))
        )

        df.write.mode("overwrite").parquet(BRONZE_PATH)
        spark.stop()

        return "Bronze created"

    # ---------- TASK 2 : SILVER ----------
    @task
    def bronze_to_silver():
        spark = get_spark("bronze_to_silver")

        df = spark.read.parquet(BRONZE_PATH)

        df_clean = (
            df.orderBy("open_time")
              .dropDuplicates(["open_time"])
              .dropna()
        )

        df_clean.write.mode("overwrite").parquet(SILVER_PATH)
        spark.stop()

        return "Silver created"

    # ---------- TASK 3 : FEATURES ----------
    @task
    def create_features():
        spark = get_spark("feature_engineering")

        df = spark.read.parquet(SILVER_PATH)
        w = Window.orderBy("open_time")

        df_feat = (
            df
            .withColumn("close_t_plus_10", F.lead("close", 10).over(w))
            .withColumn("close_prev", F.lag("close", 1).over(w))
            .withColumn(
                "return_1m",
                (F.col("close") - F.col("close_prev")) / F.col("close_prev")
            )
        )

        w5 = w.rowsBetween(-4, 0)
        w10 = w.rowsBetween(-9, 0)

        df_feat = (
            df_feat
            .withColumn("ma_5", F.avg("close").over(w5))
            .withColumn("ma_10", F.avg("close").over(w10))
            .withColumn(
                "taker_ratio",
                F.col("taker_buy_base_volume") / F.col("volume")
            )
            .dropna()
        )

        df_feat.write.mode("overwrite").parquet(FEATURES_PATH)
        spark.stop()

        return "Features created"

    # ---------- TASK 4 : TRAIN ----------
    @task
    def train_model():
        spark = get_spark("train_model")

        df = spark.read.parquet(FEATURES_PATH)

        features_cols = [
            "return_1m", "ma_5", "ma_10",
            "volume", "close_prev",
            "number_of_trades", "taker_ratio"
        ]

        w = Window.orderBy("open_time")
        df = df.withColumn("row_id", F.row_number().over(w))

        cutoff = int(df.count() * 0.8)
        train_df = df.filter(F.col("row_id") <= cutoff)
        test_df = df.filter(F.col("row_id") > cutoff)

        assembler = VectorAssembler(
            inputCols=features_cols,
            outputCol="features"
        )

        train_data = assembler.transform(train_df).select("features", "close_t_plus_10")
        test_data = assembler.transform(test_df).select("features", "close_t_plus_10")

        lr = LinearRegression(labelCol="close_t_plus_10")
        model = lr.fit(train_data)

        predictions = model.transform(test_data)

        for metric in ["rmse", "mae", "r2"]:
            score = RegressionEvaluator(
                labelCol="close_t_plus_10",
                predictionCol="prediction",
                metricName=metric
            ).evaluate(predictions)
            print(f"{metric.upper()} : {score}")

        model.write().overwrite().save(MODEL_PATH)
        spark.stop()

        return "Model trained"

    # ---------- PIPELINE ----------
    collect_bronze() >> bronze_to_silver() >> create_features() >> train_model()


btc_pipeline()
