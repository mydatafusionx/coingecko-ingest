from pyspark.sql import SparkSession

def main():
    # Inicializa a sessão do Spark com suporte a Delta Lake e desabilita métricas do Prometheus
    spark = SparkSession.builder \
        .appName("CheckDeltaTable") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.metrics.conf.*.sink.prometheusServlet.class", "org.apache.spark.metrics.sink.PrometheusServlet") \
        .config("spark.metrics.conf.*.sink.prometheusServlet.path", "/metrics/prometheus") \
        .config("spark.metrics.conf.master.sink.prometheusServlet.path", "metrics/master/prometheus") \
        .config("spark.metrics.conf.applications.sink.prometheusServlet.path", "metrics/applications/prometheus") \
        .config("spark.ui.prometheus.enabled", "false") \
        .config("spark.metrics.namespace", "") \
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
