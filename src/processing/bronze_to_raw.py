from pyspark.sql import SparkSession
from pyspark.sql.functions import col


'''
BRONZE → RAW (ou SILVER) = structuration
🎯 Objectif

➡️ Transformer les données brutes en tableau propre
➡️ Typage
➡️ Déduplication
➡️ Ordonnancement temporel
'''


spark = SparkSession.builder.appName("btc_raw_silver").getOrCreate()

# 1) Lire le Bronze
df_bronze = spark.read.parquet("data/bronze/btc_minute_data.parquet")

# 2) Colonnes utiles + types propres
df_raw = df_bronze.select(
    col("open_time").cast("timestamp"),
    col("close_time").cast("timestamp"),
    col("open").cast("double"),
    col("high").cast("double"),
    col("low").cast("double"),
    col("close").cast("double"),
    col("volume").cast("double"),
    col("quote_asset_volume").cast("double"),
    col("number_of_trades").cast("int"),
    col("taker_buy_base_volume").cast("double"),
    col("taker_buy_quote_volume").cast("double")
)

# 3) Trier par temps + enlever doublons
df_raw = df_raw.orderBy("open_time").dropDuplicates(["open_time"])

# 4) Sauvegarder la table btc_raw
df_raw.write.mode("overwrite").parquet("data/silver/btc_raw/")
print("Table btc_raw sauvegardée")