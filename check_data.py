import os
import json
from pyspark.sql import SparkSession

# Configuração básica do Spark
spark = SparkSession.builder \
    .appName("DataCheck") \
    .config("spark.sql.warehouse.dir", os.path.join(os.getcwd(), "spark-warehouse")) \
    .getOrCreate()

# Caminhos dos dados
base_dir = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(base_dir, "data/raw")
delta_dir = os.path.join(base_dir, "data/delta")

print("\n=== Verificando arquivos JSON brutos ===")
raw_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]
print(f"Arquivos encontrados em {raw_dir}:")
for file in raw_files:
    file_path = os.path.join(raw_dir, file)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            print(f"- {file}: {len(data) if isinstance(data, list) else 'objeto JSON'}")
    except Exception as e:
        print(f"- {file}: Erro ao ler - {str(e)}")

# Verificar se existem tabelas Delta
print("\n=== Verificando tabelas Delta ===")
delta_tables = []
for root, dirs, files in os.walk(delta_dir):
    if "_delta_log" in dirs:
        table_path = os.path.relpath(root, delta_dir)
        delta_tables.append(table_path)
        
        try:
            # Tenta ler a tabela Delta
            df = spark.read.format("delta").load(root)
            print(f"\nTabela Delta: {table_path}")
            print(f"Número de registros: {df.count()}")
            print("Schema:")
            df.printSchema()
            print("Amostra de dados:")
            df.show(5, truncate=False)
        except Exception as e:
            print(f"Erro ao ler a tabela Delta em {table_path}: {str(e)}")

if not delta_tables:
    print("Nenhuma tabela Delta encontrada.")
    print("\n=== Executando transformação manualmente ===")
    try:
        from pyspark.sql.functions import col, from_unixtime, to_date, lit, explode
        
        # Exemplo de transformação de um arquivo de preços simples
        simple_price_file = os.path.join(raw_dir, [f for f in os.listdir(raw_dir) if 'simple_price' in f][0])
        print(f"\nProcessando arquivo: {simple_price_file}")
        
        # Lê o arquivo JSON
        df = spark.read.option("multiLine", True).json(simple_price_file)
        
        # Processa os dados
        df = df.select(explode(col("*")).alias("coin_id", "data")) \
               .select("coin_id", "data.*") \
               .withColumn("timestamp", from_unixtime(col("last_updated").cast("long")))
        
        # Mostra os resultados
        print("Dados processados:")
        df.show(5, truncate=False)
        
        # Salva como Delta
        output_path = os.path.join(delta_dir, "prices")
        df.write.format("delta").mode("overwrite").save(output_path)
        print(f"\nDados salvos em formato Delta em: {output_path}")
        
    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")

print("\n=== Verificação concluída ===")
spark.stop()
