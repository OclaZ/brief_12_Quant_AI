from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql import SparkSession
'''
3️⃣ RAW → FEATURES = intelligence
➡️ Transformer les données en variables exploitables par un modèle ML

🔹Objectif
    Calculs statistiques
    Fenêtres temporelles
    Indicateurs financiers
'''
# sauvgarder data f  postgres mancreyich la cible 
spark = SparkSession.builder.appName("btc_features").getOrCreate()
# 1) Relire btc_raw
df_raw = spark.read.parquet("data/silver/btc_raw/")

# 2) Fenêtre ordonnée par le temps
w_time = Window.orderBy("open_time")

# 3) Cible : close_t_plus_10 Prix futur T+10 min :
df_feat = df_raw.withColumn("close_t_plus_10",F.lead("close", 10).over(w_time))

# 4) Return (variation relative)
df_feat = df_feat.withColumn("close_prev",F.lag("close", 1).over(w_time))
df_feat = df_feat.withColumn("return_1m",(df_feat["close"] - df_feat["close_prev"]) / df_feat["close_prev"])

# 5) Moyennes mobiles 5 et 10 minutes
w_5 = Window.orderBy("open_time").rowsBetween(-4, 0)
w_10 = Window.orderBy("open_time").rowsBetween(-9, 0)

df_feat = df_feat.withColumn("ma_5",F.avg("close").over(w_5)).withColumn("ma_10",F.avg("close").over(w_10))

# 6) Taker ratio
df_feat = df_feat.withColumn("taker_ratio",F.col("taker_buy_base_volume") / F.col("volume"))

# 7) Nettoyer les lignes incomplètes (cible null, début de série, etc.)
df_feat = df_feat.dropna(subset=["close_t_plus_10", "return_1m", "ma_5", "ma_10", "taker_ratio"])

# 8) Sauvegarder la table btc_features
df_feat.write.mode("overwrite").parquet("data/silver/btc_features/")
print("Table btc_features sauvegardée")
