import os
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, from_json, explode
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, MapType

def setup_spark():
    """Configura e retorna uma sessão Spark com suporte a Delta Lake."""
    return (
        SparkSession.builder 
        .appName("FixCoinsProcessing") 
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") 
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")  # Para compatibilidade com formatos de data
        .config("spark.sql.legacy.parquet.datetimeRebaseModeInWrite", "LEGACY")
        .config("spark.metrics.conf", "/dev/null")  # Desabilita métricas
        .config("spark.metrics.namespace", "")  # Desabilita namespaces de métricas
        .config("spark.metrics.staticSources.enabled", "false")  # Desabilita fontes estáticas de métricas
        .config("spark.ui.prometheus.enabled", "false")  # Desabilita UI do Prometheus
        .getOrCreate()
    )

def read_json_file(spark, file_path):
    """Lê um arquivo JSON e retorna um DataFrame."""
    print(f"Lendo arquivo: {file_path}")
    
    # Primeiro, lê o arquivo como texto para verificar o conteúdo
    raw_content = spark.sparkContext.wholeTextFiles(file_path).collect()[0][1]
    print(f"Conteúdo bruto (primeiros 200 caracteres): {raw_content[:200]}...")
    
    try:
        # Tenta analisar o JSON para entender sua estrutura
        json_data = json.loads(raw_content)
        print(f"Tipo do JSON: {type(json_data)}")
        if isinstance(json_data, list):
            print(f"Tamanho da lista: {len(json_data)}")
            if len(json_data) > 0:
                print(f"Primeiro item: {json_data[0]}")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
    
    # Agora lê com o Spark
    df = spark.read.option("multiLine", True).json(file_path)
    print(f"Schema do DataFrame:")
    df.printSchema()
    print(f"Contagem de registros: {df.count()}")
    
    if df.count() > 0:
        print("Primeiras linhas do DataFrame:")
        df.show(5, truncate=False)
    
    return df

def process_coins_data(spark, input_path, output_path):
    """Processa os dados de moedas e salva como Delta."""
    print(f"\nProcessando dados de moedas de: {input_path}")
    
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
    
    # Lê o arquivo JSON
    df = read_json_file(spark, file_path)
    
    # Se o DataFrame estiver vazio, tenta uma abordagem alternativa
    if df.count() == 0:
        print("\nTentando abordagem alternativa para ler o JSON...")
        # Lê o arquivo como texto e faz o parse manual
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Tenta carregar como JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                print(f"Carregado como lista com {len(data)} itens")
                # Cria um RDD a partir da lista e converte para DataFrame
                rdd = spark.sparkContext.parallelize(data)
                df = spark.read.json(rdd)
                print("Schema após conversão alternativa:")
                df.printSchema()
                print(f"Total de registros: {df.count()}")
                if df.count() > 0:
                    df.show(5, truncate=False)
        except Exception as e:
            print(f"Erro ao processar JSON: {e}")
    
    # Se ainda estiver vazio, tenta outra abordagem
    if df.count() == 0:
        print("\nTentando carregar com inferSchema...")
        df = spark.read.option("inferSchema", "true").option("multiLine", "true").json(file_path)
        print(f"Total de registros após inferSchema: {df.count()}")
        if df.count() > 0:
            df.printSchema()
            df.show(5, truncate=False)
    
    # Se ainda não tivermos dados, saímos
    if df.count() == 0:
        print("\nNão foi possível carregar dados válidos do arquivo.")
        return
    
    # Tenta selecionar as colunas necessárias
    try:
        # Verifica se as colunas existem
        required_columns = ["id", "symbol", "name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"\nColunas ausentes no DataFrame: {missing_columns}")
            print("Colunas disponíveis:", df.columns)
            
            # Tenta encontrar colunas com nomes semelhantes
            print("\nTentando encontrar colunas correspondentes...")
            for col_name in required_columns:
                matching = [c for c in df.columns if col_name.lower() in c.lower()]
                print(f"Colunas parecidas com '{col_name}': {matching}")
            
            # Se não encontrar as colunas, tanta uma abordagem mais genérica
            print("\nTentando abordagem genérica...")
            df = df.selectExpr("*")
            print("Colunas disponíveis:", df.columns)
            
            # Se ainda não tivermos as colunas necessárias, saímos
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"\nNão foi possível encontrar as colunas necessárias: {missing_columns}")
                return
        
        # Seleciona apenas as colunas necessárias
        df = df.select("id", "symbol", "name")
        
        # Adiciona um timestamp para rastreamento
        from pyspark.sql.functions import current_timestamp
        df = df.withColumn("ingestion_timestamp", current_timestamp())
        
        # Mostra o esquema e algumas linhas
        print("\nSchema final:")
        df.printSchema()
        print(f"\nTotal de registros processados: {df.count()}")
        print("\nAmostra dos dados:")
        df.show(5, truncate=False)
        
        # Salva como Delta
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
        # Processa os dados de moedas
        process_coins_data(spark, raw_path, delta_path)
        
    finally:
        # Encerra a sessão Spark
        spark.stop()

if __name__ == "__main__":
    main()
