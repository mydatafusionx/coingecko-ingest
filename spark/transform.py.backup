import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime, to_date, lit, explode, array, struct
from delta import configure_spark_with_delta_pip

# Configura caminhos relativos ao diretório do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data/raw/")
DELTA_PATH = os.path.join(BASE_DIR, "data/delta/market_prices")

# Configuração do Spark para execução local
builder = (
    SparkSession.builder.appName("CoinGeckoTransform")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.warehouse.dir", os.path.join(BASE_DIR, "spark-warehouse"))
    .config("spark.driver.memory", "2g")
    .config("spark.executor.memory", "2g")
)

# Configura o Delta Lake
spark = configure_spark_with_delta_pip(builder).getOrCreate()

print("Lendo arquivos JSON de:", RAW_PATH)

# Lista todos os arquivos JSON no diretório raw
json_files = [os.path.join(RAW_PATH, f) for f in os.listdir(RAW_PATH) 
             if f.endswith('.json') and os.path.isfile(os.path.join(RAW_PATH, f))]

print(f"Arquivos encontrados: {json_files}")

# Processa cada arquivo JSON individualmente
for json_file in json_files:
    print(f"Processando arquivo: {json_file}")
    
    # Lê o arquivo JSON
    df = spark.read.option("multiLine", True).json(json_file)
    
    # Exibe o schema e as primeiras linhas para depuração
    print(f"Schema do arquivo {json_file}:")
    df.printSchema()
    print(f"Total de registros: {df.count()}")
    
    # Processa o arquivo de acordo com seu tipo
    if "coins_list" in json_file:
        # Processa a lista de moedas
        df = df.select("id", "symbol", "name")
        df.show(5, truncate=False)
        
        # Salva como Delta
        (
            df.write.format("delta")
            .mode("overwrite")
            .save(os.path.join(DELTA_PATH, "coins"))
        )
        print(f"Dados salvos em: {os.path.join(DELTA_PATH, 'coins')}")
        
    elif "simple_price" in json_file:
        # Processa preços simples
        df = df.select(explode(col("*")))\
               .select("key as coin_id", "value.*")\
               .withColumn("timestamp", lit(from_unixtime(lit(0) + (col("last_updated") / 1000))))
        
        # Converte colunas para double
        for col_name in df.columns:
            if col_name not in ["coin_id", "timestamp"]:
                df = df.withColumn(col_name, col(col_name).cast("double"))
        
        df.show(5, truncate=False)
        
        # Salva como Delta
        (
            df.write.format("delta")
            .mode("overwrite")
            .save(os.path.join(DELTA_PATH, "prices"))
        )
        print(f"Dados salvos em: {os.path.join(DELTA_PATH, 'prices')}")
        
    elif "market_chart" in json_file:
        # Processa gráficos de mercado
        coin_id = os.path.basename(json_file).split('_')[2]  # Extrai o nome da moeda do nome do arquivo
        
        # Processa preços
        if "prices" in df.columns:
            prices_df = df.select("prices").withColumn("price_data", explode(col("prices")))
            prices_df = prices_df.select(
                lit(coin_id).alias("coin_id"),
                (col("price_data")[0] / 1000).cast("timestamp").alias("timestamp"),
                col("price_data")[1].alias("price")
            )
            prices_df = prices_df.withColumn("date", to_date("timestamp"))
            
            prices_df.show(5, truncate=False)
            
            # Salva preços como Delta
            (
                prices_df.write.format("delta")
                .mode("overwrite")
                .partitionBy("coin_id", "date")
                .save(os.path.join(DELTA_PATH, f"market_charts/{coin_id}/prices"))
            )
            print(f"Dados de preços salvos em: {os.path.join(DELTA_PATH, f'market_charts/{coin_id}/prices')}")
        
        # Processa volumes (se existir)
        if "total_volumes" in df.columns:
            volumes_df = df.select("total_volumes").withColumn("volume_data", explode(col("total_volumes")))
            volumes_df = volumes_df.select(
                lit(coin_id).alias("coin_id"),
                (col("volume_data")[0] / 1000).cast("timestamp").alias("timestamp"),
                col("volume_data")[1].alias("volume")
            )
            volumes_df = volumes_df.withColumn("date", to_date("timestamp"))
            
            volumes_df.show(5, truncate=False)
            
            # Salva volumes como Delta
            (
                volumes_df.write.format("delta")
                .mode("overwrite")
                .partitionBy("coin_id", "date")
                .save(os.path.join(DELTA_PATH, f"market_charts/{coin_id}/volumes"))
            )
            print(f"Dados de volume salvos em: {os.path.join(DELTA_PATH, f'market_charts/{coin_id}/volumes')}")

print("Processamento concluído com sucesso!")
spark.stop()
