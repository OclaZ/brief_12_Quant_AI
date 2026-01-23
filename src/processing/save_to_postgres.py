from pyspark.sql import SparkSession

def save_to_postgres_task():
    spark = SparkSession.builder \
        .appName("save_to_postgres") \
        .config("spark.jars", "/opt/airflow/spark_libs/postgresql-42.6.0.jar") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

    print("Spark session created successfully")

    # JDBC connection
    jdbc_url = "jdbc:postgresql://quant_postgres:5432/silver_db"
    connection_properties = {
        "user": "user",
        "password": "silver_db",
        "driver": "org.postgresql.Driver"
    }

    # Load features from Silver
    df_features = spark.read.parquet("/opt/airflow/data/silver/btc_features/")
    print(f"Data loaded: {df_features.count()} rows")
    df_features.show(5)

    # Save to Postgres
    df_features.write.jdbc(
        url=jdbc_url,
        table="btc_features",
        mode="overwrite",
        properties=connection_properties
    )
    print("Data saved to Postgres successfully")

    spark.stop()
    print("Spark session stopped")