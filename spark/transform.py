import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime, to_date
from delta import configure_spark_with_delta_pip

RAW_PATH = "/data/raw/"
DELTA_PATH = "/data/delta/market_prices"

builder = (
    SparkSession.builder.appName("CoinGeckoTransform")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Exemplo: lê todos arquivos JSON do RAW_PATH
df = spark.read.option("multiLine", True).json(RAW_PATH + "*.json")

# Conversões e casts (exemplo)
if "prices" in df.columns:
    df = df.withColumn("timestamp", from_unixtime(col("prices")[0][0]/1000))
    df = df.withColumn("date", to_date(col("timestamp")))
    df = df.withColumn("coin_id", col("id"))

# Escreve particionado por coin_id e date
(
    df.write.format("delta")
    .mode("overwrite")
    .partitionBy("coin_id", "date")
    .option("overwriteSchema", "true")
    .save(DELTA_PATH)
)

spark.stop()
