from pyspark.sql import SparkSession

def save_to_postgres_task():
    # 1. Création de la session avec le fix pour les nanosecondes
    spark = SparkSession.builder \
        .appName("SaveToPostgres") \
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED") \
        .config("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED") \
        .getOrCreate()

    SILVER_PATH = "/opt/airflow/data/silver/btc_features"

    # 2. Lecture du fichier (Spark va maintenant gérer le format INT64)
    df = spark.read.parquet(SILVER_PATH)

    # 3. Conversion en Pandas pour l'écriture dans Postgres
    # (Note: Postgres gère très bien les microsecondes)
    pdf = df.toPandas()

    # 4. Sauvegarde via SQLAlchemy (Vérifie bien tes identifiants ici)
    from sqlalchemy import create_engine
    engine = create_engine("postgresql://postgres:admin@postgres:5432/quant_db")
    
    pdf.to_sql('btc_features', engine, if_exists='replace', index=False)
    
    spark.stop()