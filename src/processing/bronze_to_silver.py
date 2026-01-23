from pyspark.sql import SparkSession
from pyspark.sql.functions import col

def transform_silver():
    spark = SparkSession.builder.appName("silver_layer").master("local[*]").getOrCreate()

    df_bronze = spark.read.parquet("data/bronze/bronze.parquet")

    df_clean = (
        df_bronze
        .orderBy("open_time")
        .dropDuplicates(["open_time"])
        .dropna()
    )

    df_clean.write.mode("overwrite").parquet("data/silver/btc_silver")

    spark.stop()
    return "Silver layer created"