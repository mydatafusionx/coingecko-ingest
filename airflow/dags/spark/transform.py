import sys
import os
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime, to_date, lit, explode, array, struct, to_json, when
from pyspark.sql.types import DoubleType, LongType

# Tenta importar o importlib_metadata ou fornece uma mensagem de erro clara
try:
    import importlib_metadata
except ImportError:
    print("ERRO: O pacote 'importlib_metadata' não está instalado.")
    print("Por favor, instale-o executando: pip install importlib_metadata")
    sys.exit(1)

# Agora importa o Delta Lake
try:
    from delta import configure_spark_with_delta_pip
except ImportError as e:
    print(f"ERRO ao importar o Delta Lake: {e}")
    print("Certifique-se de que o Delta Lake está instalado corretamente.")
    sys.exit(1)

# Verifica se está rodando em container (VPS) ou localmente
IS_CONTAINER = os.path.exists('/.dockerenv') or os.path.exists('/data')

# Configura caminhos relativos ao ambiente
if IS_CONTAINER:
    # Configuração para o ambiente do container (VPS)
    BASE_DIR = "/data"
    RAW_PATH = os.path.join(BASE_DIR, "raw/")
    DELTA_PATH = os.path.join(BASE_DIR, "delta/market_prices")
else:
    # Configuração para ambiente local de desenvolvimento
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_PATH = os.path.join(BASE_DIR, "data/raw/")
    DELTA_PATH = os.path.join(BASE_DIR, "data/delta/market_prices")

# Cria diretórios necessários se não existirem
os.makedirs(RAW_PATH, exist_ok=True)
os.makedirs(DELTA_PATH, exist_ok=True)

# Configuração do Spark para execução local
builder = (
    SparkSession.builder.appName("CoinGeckoTransform")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.warehouse.dir", os.path.join(BASE_DIR, "spark-warehouse"))
    .config("spark.driver.memory", "2g")
    .config("spark.executor.memory", "2g")
    # Desativa as métricas do Prometheus para evitar erros
    .config("spark.metrics.conf", "/dev/null")
    .config("spark.metrics.namespace", "")
    .config("spark.metrics.staticSources.enabled", "false")
    .config("spark.ui.prometheus.enabled", "false")
)

# Configura o Delta Lake
spark = configure_spark_with_delta_pip(builder).getOrCreate()

print("Lendo arquivos JSON de:", RAW_PATH)

# Lista todos os arquivos JSON no diretório raw
json_files = [os.path.join(RAW_PATH, f) for f in os.listdir(RAW_PATH) 
             if f.endswith('.json') and os.path.isfile(os.path.join(RAW_PATH, f))]

print(f"Arquivos encontrados: {json_files}")

def process_simple_price(json_file_path):
    """Processa arquivos de preço simples do CoinGecko"""
    print(f"Processando arquivo de preços simples: {json_file_path}")
    
    try:
        # Lê o arquivo JSON como texto
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
        
        # Cria uma lista para armazenar os dados transformados
        rows = []
        
        # Itera sobre cada moeda no JSON
        for coin_id, prices in json_data.items():
            # Adiciona o ID da moeda ao dicionário de preços
            price_data = {"coin_id": coin_id}
            # Adiciona todos os preços ao dicionário, convertendo para float para evitar problemas de tipo
            for price_key, price_value in prices.items():
                if price_value is not None:
                    if isinstance(price_value, dict):
                        # Se o valor for um dicionário, converte todos os valores numéricos para float
                        for k, v in price_value.items():
                            if isinstance(v, (int, float)):
                                price_value[k] = float(v)
                    price_data[price_key] = price_value
            rows.append(price_data)
        
        if not rows:
            print("Nenhum dado encontrado no arquivo.")
            return
            
        # Cria um DataFrame a partir da lista de dicionários
        df = spark.createDataFrame(rows)
        
        # Converte explicitamente todas as colunas numéricas para double
        for col_name in df.columns:
            if col_name != "coin_id":
                df = df.withColumn(col_name, col(col_name).cast("double"))
        
        # Exibe o schema e as primeiras linhas para depuração
        print("Schema do DataFrame de preços:")
        df.printSchema()
        print("Primeiras linhas dos dados de preços:")
        df.show(truncate=False)
        
        # Salva como Delta
        try:
            (
                df.write.format("delta")
                .mode("overwrite")
                .save(os.path.join(DELTA_PATH, "prices"))
            )
            print(f"Dados de preços salvos em: {os.path.join(DELTA_PATH, 'prices')}")
        except Exception as e:
            print(f"Erro ao salvar dados Delta: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar o arquivo JSON {json_file_path}: {str(e)}")
        return
    except Exception as e:
        print(f"Erro ao processar o arquivo {json_file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return

def process_coins_list(json_file_path):
    """Processa a lista de moedas do CoinGecko"""
    print(f"Processando lista de moedas: {json_file_path}")
    
    # Lê o arquivo JSON
    df = spark.read.option("multiLine", True).json(json_file_path)
    
    # Seleciona apenas as colunas necessárias
    df = df.select("id", "symbol", "name")
    
    # Exibe o schema e as primeiras linhas para depuração
    print("Schema do DataFrame de moedas:")
    df.printSchema()
    print("Primeiras linhas dos dados de moedas:")
    df.show(truncate=False)
    
    # Salva como Delta
    (
        df.write.format("delta")
        .mode("overwrite")
        .save(os.path.join(DELTA_PATH, "coins"))
    )
    print(f"Dados de moedas salvos em: {os.path.join(DELTA_PATH, 'coins')}")

def process_market_chart(json_file_path):
    """Processa dados de gráfico de mercado do CoinGecko"""
    print(f"Processando gráfico de mercado: {json_file_path}")
    
    # Extrai o ID da moeda do nome do arquivo
    coin_id = os.path.basename(json_file_path).split('_')[2]
    
    # Lê o arquivo JSON
    df = spark.read.option("multiLine", True).json(json_file_path)
    
    # Processa preços
    if "prices" in df.columns:
        prices_df = df.select("prices").withColumn("price_data", explode(col("prices")))
        prices_df = prices_df.select(
            lit(coin_id).alias("coin_id"),
            (col("price_data")[0] / 1000).cast("timestamp").alias("timestamp"),
            col("price_data")[1].alias("price")
        )
        prices_df = prices_df.withColumn("date", to_date("timestamp"))
        
        print(f"Dados de preços para {coin_id}:")
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
        
        print(f"Dados de volume para {coin_id}:")
        volumes_df.show(5, truncate=False)
        
        # Salva volumes como Delta
        (
            volumes_df.write.format("delta")
            .mode("overwrite")
            .partitionBy("coin_id", "date")
            .save(os.path.join(DELTA_PATH, f"market_charts/{coin_id}/volumes"))
        )
        print(f"Dados de volume salvos em: {os.path.join(DELTA_PATH, f'market_charts/{coin_id}/volumes')}")

# Processa cada arquivo JSON individualmente
for json_file in json_files:
    print(f"\nProcessando arquivo: {json_file}")
    
    try:
        if "simple_price" in json_file:
            process_simple_price(json_file)
        elif "coins_list" in json_file:
            process_coins_list(json_file)
        elif "market_chart" in json_file:
            process_market_chart(json_file)
        else:
            print(f"Tipo de arquivo não reconhecido: {json_file}")
    except Exception as e:
        print(f"Erro ao processar o arquivo {json_file}: {str(e)}")
        import traceback
        traceback.print_exc()

print("\nProcessamento concluído com sucesso!")
spark.stop()
