# from pyspark.sql import SparkSession, Window
# import pyspark.sql.functions as F


# def compute_silver_features():
#     spark = SparkSession.builder.appName("silver_features").getOrCreate()
#     spark._jsc.hadoopConfiguration().set("fs.file.impl", "org.apache.hadoop.fs.RawLocalFileSystem")

# # 2. On garde ton umask habituel pour la création
#     spark._jsc.hadoopConfiguration().set("fs.permissions.umask-mode", "000")
#     #  Lire la Silver layer (TOUJOURS le dossier)
#     df = spark.read.parquet("data/silver/btc_silver")

#     # Fenêtre temporelle
#     w_time = Window.orderBy("open_time")

#     #  Target : close price à T+10 minutes
#     df_feat = df.withColumn(
#         "close_t_plus_10",
#         F.lead("close", 10).over(w_time)
#     )

#     #  Return 1 minute
#     df_feat = df_feat.withColumn(
#         "close_prev",
#         F.lag("close", 1).over(w_time)
#     )

#     df_feat = df_feat.withColumn(
#         "return_1m",
#         (F.col("close") - F.col("close_prev")) / F.col("close_prev")
#     )

#     #  Moving averages
#     w_5 = Window.orderBy("open_time").rowsBetween(-4, 0)
#     w_10 = Window.orderBy("open_time").rowsBetween(-9, 0)

#     df_feat = (
#         df_feat
#         .withColumn("ma_5", F.avg("close").over(w_5))
#         .withColumn("ma_10", F.avg("close").over(w_10))
#     )

#     #  Taker ratio
#     df_feat = df_feat.withColumn(
#         "taker_ratio",
#         F.col("taker_buy_base_volume") / F.col("volume")
#     )

#     #  Nettoyage final (features + target obligatoires)
#     df_feat = df_feat.dropna(subset=[
#         "close_t_plus_10",
#         "return_1m",
#         "close_prev",
#         "ma_5",
#         "ma_10",
#         "taker_ratio"
#     ])

#     # Sauvegarde Silver Features
#     df_feat.write.mode("overwrite").parquet(
#         "data/silver/btc_features"
#     )

#     spark.stop()


# if __name__ == "__main__":
#     compute_silver_features()


import pandas as pd
import os
import sys
import shutil
from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F

def compute_silver_features():
    input_path = "/opt/airflow/data/silver/btc_silver"
    output_path = "/opt/airflow/data/silver/btc_features"
    
    try:
        print(f"--- ETAPE 1: Lecture via Pandas (évite l'erreur NANOS) ---")
        if not os.path.exists(input_path):
            raise Exception(f"Fichier source introuvable : {input_path}")
        
        # On lit avec Pandas pour gérer les timestamps en nanosecondes
        pdf = pd.read_parquet(input_path)
        
        # Conversion cruciale : Spark ne gère pas bien les datetime64[ns]
        # On passe en microsecondes [us]
        for col in pdf.select_dtypes(include=['datetime64[ns]']).columns:
            pdf[col] = pdf[col].values.astype('datetime64[us]')

        # Initialisation Spark
        spark = SparkSession.builder.appName("silver_features").getOrCreate()
        df = spark.createDataFrame(pdf)

        # --- ETAPE 2: Transformation ---
        # Ajout d'une partition fictive pour les Window functions
        df = df.withColumn("dummy_part", F.lit(1))
        w_time = Window.partitionBy("dummy_part").orderBy("open_time")

        df_feat = df.withColumn("close_t_plus_10", F.lead("close", 10).over(w_time)) \
                    .withColumn("close_prev", F.lag("close", 1).over(w_time)) \
                    .withColumn("return_1m", (F.col("close") - F.col("close_prev")) / F.col("close_prev"))

        w_ma = Window.partitionBy("dummy_part").orderBy("open_time").rowsBetween(-9, 0)
        df_feat = df_feat.withColumn("ma_5", F.avg("close").over(Window.partitionBy("dummy_part").orderBy("open_time").rowsBetween(-4, 0))) \
                         .withColumn("ma_10", F.avg("close").over(w_ma)) \
                         .withColumn("taker_ratio", F.col("taker_buy_base_volume") / F.col("volume"))

        # Nettoyage
        df_final = df_feat.dropna(subset=["close_t_plus_10", "return_1m"]).drop("dummy_part")

        # --- ETAPE 3: Ecriture via le "Pont Pandas" (Stabilité Docker/Windows) ---
        print(f"--- ETAPE 3: Conversion et écriture vers {output_path} ---")
        pdf_output = df_final.toPandas()

        if os.path.exists(output_path):
            if os.path.isdir(output_path): shutil.rmtree(output_path)
            else: os.remove(output_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf_output.to_parquet(output_path, index=False)
        
        print("--- BRAVO : Pipeline terminée avec succès ! ---")
        spark.stop()
        return "Features layer created"

    except Exception as e:
        print(f"!!! ERREUR CRITIQUE !!! : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    compute_silver_features()