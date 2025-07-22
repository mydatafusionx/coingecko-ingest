from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'api_to_delta',
    default_args=default_args,
    description='Ingest CoinGecko API data and store as Delta Lake',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

run_java_client = BashOperator(
    task_id='run_java_client',
    bash_command='docker exec java-client java -jar /app/coin-gecko-ingest.jar',
    dag=dag,
)

run_spark_transform = BashOperator(
    task_id='run_spark_transform',
    bash_command='''
    docker exec spark-master spark-submit \
    --packages io.delta:delta-core_2.12:2.4.0 \
    --conf 'spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension' \
    --conf 'spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog' \
    /tmp/transform.py
    ''',
    dag=dag,
)

run_java_client >> run_spark_transform
