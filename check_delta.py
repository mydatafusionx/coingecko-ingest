from pyspark.sql import SparkSession
import os

def check_delta_data():
    # Initialize Spark session with Delta Lake
    builder = SparkSession.builder \
        .appName("CheckDeltaData") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    
    # Add Prometheus metrics configurations
    builder = builder.config("spark.metrics.conf", "/dev/null")
    builder = builder.config("spark.metrics.namespace", "")
    builder = builder.config("spark.metrics.staticSources.enabled", "false")
    builder = builder.config("spark.ui.prometheus.enabled", "false")
    
    # Create the Spark session
    spark = builder.getOrCreate()
    
    # Print Spark configuration for debugging
    print("Spark configuration:")
    for (key, value) in spark.sparkContext.getConf().getAll():
        print(f"{key} = {value}")
    
    # Path to Delta table
    delta_path = "/data/delta/market_prices/coins"
    
    try:
        # Read Delta table
        print(f"Reading Delta table from: {delta_path}")
        df = spark.read.format("delta").load(delta_path)
        
        # Show schema and sample data
        print("\nSchema:")
        df.printSchema()
        
        print("\nSample data (first 5 rows):")
        df.show(5, truncate=False)
        
        # Show row count
        print(f"\nTotal rows: {df.count()}")
        
        # Show the schema and columns
        print("\nTable schema:")
        df.printSchema()
        
        # Show the first 5 rows
        print("\nFirst 5 rows:")
        df.show(5, truncate=False)
        
        # Show distinct coins
        print("\nDistinct coins (first 20):")
        if "id" in df.columns:
            df.select("id").distinct().show(20, truncate=False)
        elif "coin_id" in df.columns:
            df.select("coin_id").distinct().show(20, truncate=False)
        
        # Check for timestamp or date columns
        timestamp_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if timestamp_cols:
            print(f"\nTimestamp/date columns found: {timestamp_cols}")
            for col in timestamp_cols:
                print(f"\nDistinct {col} values (first 10):")
                df.select(col).distinct().orderBy(col).show(10, truncate=False)
        
    except Exception as e:
        print(f"Error reading Delta table: {str(e)}")
    
    spark.stop()

if __name__ == "__main__":
    check_delta_data()
