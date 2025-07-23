import os
import json
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import current_timestamp

def setup_spark():
    """Configura e retorna uma sessão Spark com suporte a Delta Lake."""
    return (
        SparkSession.builder 
        .appName("ProcessCoinsList") 
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") 
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
        .config("spark.sql.legacy.parquet.datetimeRebaseModeInWrite", "LEGACY")
        .config("spark.metrics.conf", "/dev/null")
        .config("spark.metrics.namespace", "")
        .config("spark.metrics.staticSources.enabled", "false")
        .config("spark.ui.prometheus.enabled", "false")
        .getOrCreate()
    )

def read_coins_list(file_path):
    """Lê o arquivo JSON da lista de moedas e retorna um dicionário Python."""
    print(f"Lendo arquivo: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def process_coins_list(spark, input_path, output_path):
    """Processa a lista de moedas e salva como Delta."""
    print(f"\nProcessando lista de moedas de: {input_path}")
    
    # Lista todos os arquivos JSON de moedas
    coins_files = [f for f in os.listdir(input_path) if f.startswith('coins_list_') and f.endswith('.json')]
    print(f"Arquivos de moedas encontrados: {coins_files[:5]}... (total: {len(coins_files)})")
    
    if not coins_files:
        print("Nenhum arquivo de moedas encontrado!")
        return
    
    # Usa o arquivo mais recente
    latest_file = max(coins_files, key=lambda x: os.path.getmtime(os.path.join(input_path, x)))
    file_path = os.path.join(input_path, latest_file)
    print(f"\nProcessando arquivo mais recente: {latest_file}")
    
    try:
        # Lê o arquivo JSON como um dicionário Python
        coins_data = read_coins_list(file_path)
        print(f"Total de moedas encontradas: {len(coins_data)}")
        
        # Cria um RDD a partir da lista de dicionários
        rdd = spark.sparkContext.parallelize(coins_data)
        
        # Define o schema para o DataFrame
        schema = StructType([
            StructField("id", StringType(), nullable=False),
            StructField("symbol", StringType(), nullable=False),
            StructField("name", StringType(), nullable=False)
        ])
        
        # Cria o DataFrame a partir do RDD
        df = spark.createDataFrame(rdd, schema=schema)
        
        # Adiciona um timestamp de ingestão
        df = df.withColumn("ingestion_timestamp", current_timestamp())
        
        # Mostra o esquema e algumas linhas
        print("\nSchema do DataFrame:")
        df.printSchema()
        print(f"\nTotal de registros: {df.count()}")
        print("\nAmostra dos dados:")
        df.show(5, truncate=False)
        
        # Caminho de saída
        output_dir = os.path.join(output_path, "coins")
        print(f"\nSalvando em: {output_dir}")
        
        # Remove o diretório de saída se existir (para sobrescrever)
        import shutil
        if os.path.exists(output_dir):
            print(f"Removendo diretório existente: {output_dir}")
            shutil.rmtree(output_dir, ignore_errors=True)
        
        # Salva o DataFrame como Delta
        df.write.format("delta").mode("overwrite").save(output_dir)
        print("Dados salvos com sucesso!")
        
        # Verifica se os dados foram salvos corretamente
        print("\nVerificando dados salvos...")
        saved_df = spark.read.format("delta").load(output_dir)
        print(f"Total de registros salvos: {saved_df.count()}")
        saved_df.show(5, truncate=False)
        
    except Exception as e:
        print(f"\nErro ao processar os dados: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Configurações de caminho
    base_path = "/data"
    raw_path = os.path.join(base_path, "raw")
    delta_path = os.path.join(base_path, "delta/market_prices")
    
    # Cria diretórios se não existirem
    os.makedirs(raw_path, exist_ok=True)
    os.makedirs(delta_path, exist_ok=True)
    
    # Inicia a sessão Spark
    spark = setup_spark()
    
    try:
        # Processa a lista de moedas
        process_coins_list(spark, raw_path, delta_path)
    finally:
        # Encerra a sessão Spark
        spark.stop()

if __name__ == "__main__":
    main()
