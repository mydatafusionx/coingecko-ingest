from pyspark.sql import SparkSession
import os

def check_delta_tables():
    # Configuração do Spark com Delta Lake
    spark = SparkSession.builder \
        .appName("CheckDeltaTables") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.metrics.conf", "/dev/null") \
        .config("spark.metrics.namespace", "") \
        .config("spark.metrics.staticSources.enabled", "false") \
        .config("spark.ui.prometheus.enabled", "false") \
        .getOrCreate()
    
    # Caminho para as tabelas Delta
    base_path = "/data/delta/market_prices"
    
    # Verifica a tabela de moedas
    coins_path = os.path.join(base_path, "coins")
    print(f"\nVerificando tabela de moedas em: {coins_path}")
    
    try:
        # Lê a tabela Delta
        df = spark.read.format("delta").load(coins_path)
        
        # Mostra o schema
        print("\nSchema da tabela de moedas:")
        df.printSchema()
        
        # Mostra a contagem de registros
        print(f"\nTotal de registros: {df.count()}")
        
        # Mostra as primeiras 10 linhas
        print("\nPrimeiras 10 moedas:")
        df.show(10, truncate=False)
        
        # Verifica valores nulos
        print("\nContagem de valores nulos por coluna:")
        from pyspark.sql.functions import col, count, when, isnull
        df.select([count(when(isnull(c), c)).alias(c) for c in df.columns]).show()
        
    except Exception as e:
        print(f"Erro ao ler a tabela de moedas: {str(e)}")
    
    # Verifica se existem outras tabelas
    print("\nVerificando outras tabelas...")
    try:
        tables = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
        print(f"Tabelas encontradas: {tables}")
    except Exception as e:
        print(f"Erro ao listar tabelas: {str(e)}")
    
    spark.stop()

if __name__ == "__main__":
    check_delta_tables()
