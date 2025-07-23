from pyspark.sql import SparkSession

def main():
    # Inicializa a sessão do Spark com suporte a Delta Lake
    spark = SparkSession.builder \
        .appName("CheckDeltaTable") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

    try:
        # Caminho para a tabela Delta
        delta_path = "/data/delta/market_prices/market_charts/bitcoin/prices"
        
        # Lê a tabela Delta
        print(f"Lendo dados da tabela Delta em: {delta_path}")
        df = spark.read.format("delta").load(delta_path)
        
        # Mostra o esquema
        print("\nEsquema da tabela:")
        df.printSchema()
        
        # Conta o número de registros
        count = df.count()
        print(f"\nTotal de registros: {count}")
        
        # Mostra as primeiras 5 linhas
        if count > 0:
            print("\nPrimeiras 5 linhas:")
            df.show(5, truncate=False)
        
        # Mostra as partições
        print("\nPartições disponíveis:")
        df.select("coin_id", "date").distinct().orderBy("date").show(truncate=False)
        
    except Exception as e:
        print(f"Erro ao ler a tabela Delta: {str(e)}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
