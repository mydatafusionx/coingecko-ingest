import os
from datetime import datetime
from functools import reduce
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, TimestampType
from pyspark.sql.functions import col, from_unixtime, to_date, lit, explode, map_keys, map_from_entries, array, current_timestamp

# Configuração do Spark com Delta Lake
spark = SparkSession.builder \
    .appName("CoinGeckoTransform") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0") \
    .getOrCreate()

# Caminhos dos dados
BASE_DIR = "/opt/bitnami/spark/data"
RAW_PATH = os.path.join(BASE_DIR, "raw")
DELTA_PATH = os.path.join(BASE_DIR, "delta")

print("Lendo arquivos JSON de:", RAW_PATH)

# Lista todos os arquivos JSON no diretório raw
try:
    json_files = [f for f in os.listdir(RAW_PATH) if f.endswith('.json')]
    print(f"Arquivos encontrados: {json_files}")
    
    # Processa cada arquivo JSON individualmente
    for json_file in json_files:
        file_path = os.path.join(RAW_PATH, json_file)
        print(f"\nProcessando arquivo: {json_file}")
        
        # Lê o arquivo JSON
        df = spark.read.option("multiLine", True).json(file_path)
        
        # Exibe o schema e contagem de registros
        print("Schema do arquivo:")
        df.printSchema()
        print(f"Total de registros: {df.count()}")
        
        # Processa o arquivo de acordo com seu tipo
        if "coins_list" in json_file:
            # Processa a lista de moedas
            df = df.select("id", "symbol", "name")
            df.show(5, truncate=False)
            
            # Salva como Delta
            output_path = os.path.join(DELTA_PATH, "coins")
            (
                df.write.format("delta")
                .mode("overwrite")
                .save(output_path)
            )
            print(f"Dados salvos em formato Delta em: {output_path}")
            
        elif "simple_price" in json_file:
            # Processa preços simples
            # O arquivo tem a estrutura: {"bitcoin": {"usd": 119800}, "ethereum": {"usd": 3715.55}}
            # Vamos extrair cada moeda e seu preço
            
            # Lê o arquivo como texto para extrair as chaves (nomes das moedas)
            with open(file_path, 'r') as f:
                import json
                data = json.load(f)
                coins = list(data.keys())
            
            # Cria uma lista de tuplas (coin_id, usd_price)
            price_data = [(coin, float(data[coin]['usd']), int(datetime.now().timestamp())) 
                         for coin in coins if 'usd' in data[coin]]
            
            # Cria o DataFrame a partir da lista de tuplas
            if price_data:
                df = spark.createDataFrame(
                    price_data,
                    schema=["coin_id", "usd", "timestamp"]
                )
                df = df.withColumn("timestamp", from_unixtime(col("timestamp")).cast("timestamp"))
            else:
                # Se não houver dados, cria um DataFrame vazio com o schema esperado
                schema = StructType([
                    StructField("coin_id", StringType()),
                    StructField("usd", DoubleType()),
                    StructField("timestamp", TimestampType())
                ])
                df = spark.createDataFrame([], schema)
            
            df.show(5, truncate=False)
            
            # Salva como Delta
            output_path = os.path.join(DELTA_PATH, "prices")
            (
                df.write.format("delta")
                .mode("overwrite")
                .save(output_path)
            )
            print(f"Dados salvos em formato Delta em: {output_path}")
            
        elif "market_chart" in json_file:
            # Processa gráficos de mercado
            coin_id = json_file.split('_')[2]  # Extrai o nome da moeda do nome do arquivo
            
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
                output_path = os.path.join(DELTA_PATH, f"market_charts/{coin_id}/prices")
                (
                    prices_df.write.format("delta")
                    .mode("overwrite")
                    .partitionBy("coin_id", "date")
                    .save(output_path)
                )
                print(f"Dados de preços salvos em: {output_path}")
            
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
                output_path = os.path.join(DELTA_PATH, f"market_charts/{coin_id}/volumes")
                (
                    volumes_df.write.format("delta")
                    .mode("overwrite")
                    .partitionBy("coin_id", "date")
                    .save(output_path)
                )
                print(f"Dados de volume salvos em: {output_path}")
    
    print("\n=== Processamento concluído com sucesso! ===")
    
    # Lista as tabelas Delta criadas
    print("\nTabelas Delta criadas:")
    for root, dirs, files in os.walk(DELTA_PATH):
        if "_delta_log" in dirs:
            print(f"- {os.path.relpath(root, DELTA_PATH)}")
    
except Exception as e:
    print(f"\n=== Erro durante o processamento ===")
    print(f"Tipo do erro: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    raise e

finally:
    # Encerra a sessão do Spark
    spark.stop()
