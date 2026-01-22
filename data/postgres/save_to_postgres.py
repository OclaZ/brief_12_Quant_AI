from pyspark.sql import SparkSession



Spark = SparkSession.builder \
    .appName("save_to_postgres") \
    .config("spark.jars", "/home/dev_team/spark_libs/postgresql-42.6.0.jar") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()
print("session created successfully")


jdbc_url = "jdbc:postgresql://postgres-silver:5432/silver_db"
connection_properties = {
    "user":"user",
    "password":"silver_db",
    "driver":"org.postgresql.Driver"
}
print("connection properties set successfully")

df_features = Spark.read.parquet("data/silver/btc_features/")
print(f"data loaded : {df_features.count()} rows")
df_features.show(5)

df_features.write.jdbc(url=jdbc_url,
                      table="btc_features",
                      mode="overwrite",
                      properties=connection_properties)
print("data saved to postgres successfully")



# Verify the data
# df_check = Spark.read.jdbc(url=jdbc_url,
#                            table="btc_features",
#                            properties=connection_properties)
# print(f"data read from postgres : {df_check.count()} rows")
# df_check.show(5)
# Spark.stop()
# print("session stopped")





