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
    bash_command="""
    # Ensure the container is running
    if ! docker ps | grep -q 'java-client'; then
        # Start the container if it exists, otherwise create and start it
        if docker ps -a | grep -q 'java-client'; then
            docker start java-client
        else
            echo "Error: java-client container does not exist. Please ensure it's created before running this DAG."
            exit 1
        fi
        # Wait for the container to be fully started
        sleep 5
    fi
    
    # Execute the Java application in the container with rate limiting and retries
    MAX_RETRIES=3
    RETRY_DELAY=60  # seconds
    
    for i in $(seq 1 $MAX_RETRIES); do
        echo "Attempt $i of $MAX_RETRIES"
        
        # Execute the Java application with rate limiting
        OUTPUT=$(docker exec java-client sh -c "java $JAVA_OPTS -jar /app/app.jar 2>&1")
        EXIT_CODE=$?
        
        # Check if the command was successful
        if [ $EXIT_CODE -eq 0 ]; then
            echo "Java application executed successfully"
            echo "$OUTPUT"
            exit 0
        fi
        
        # Check if we've hit the rate limit
        if echo "$OUTPUT" | grep -q "429 Too Many Requests"; then
            echo "Rate limit hit. Waiting $RETRY_DELAY seconds before retry..."
            sleep $RETRY_DELAY
            # Increase delay for next retry (exponential backoff)
            RETRY_DELAY=$((RETRY_DELAY * 2))
        else
            # For other errors, exit with the error
            echo "Error executing Java application:"
            echo "$OUTPUT"
            exit $EXIT_CODE
        fi
    done
    
    # If we get here, all retries failed
    echo "Failed to execute Java application after $MAX_RETRIES attempts"
    exit 1
    """,
    dag=dag,
    retries=2,  # Number of retries for the entire task
    retry_delay=timedelta(minutes=5),  # Time between retries
)

run_spark_transform = BashOperator(
    task_id='run_spark_transform',
    bash_command='''
    # Print current directory and spark directory contents for debugging
    echo "Current directory: $(pwd)"
    echo "Contents of /opt/airflow/dags/spark:"
    ls -la /opt/airflow/dags/spark/ || echo "Failed to list spark directory"
    
    # Copy the transform.py script to the spark-master container
    if [ -f "/opt/airflow/dags/spark/transform.py" ]; then
        echo "Copying transform.py to spark-master container..."
        docker cp /opt/airflow/dags/spark/transform.py spark-master:/tmp/transform.py
        
        # Verify the file was copied
        echo "Verifying file was copied to spark-master container:"
        docker exec spark-master ls -la /tmp/transform.py || { echo "File not found in container"; exit 1; }
        
        # Run the Spark job with retry logic
        MAX_RETRIES=3
        RETRY_DELAY=60  # seconds
        
        for i in $(seq 1 $((MAX_RETRIES + 1))); do
            echo "[Attempt $i of $((MAX_RETRIES + 1))] Running Spark job..."
            
            # Run Spark job with error output captured
            OUTPUT=$(docker exec spark-master spark-submit \
                --packages io.delta:delta-core_2.12:2.4.0 \
                --conf 'spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension' \
                --conf 'spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog' \
                /tmp/transform.py 2>&1)
            EXIT_CODE=$?
            
            # Check if the command was successful
            if [ $EXIT_CODE -eq 0 ]; then
                echo "Spark job completed successfully"
                echo "$OUTPUT"
                exit 0
            fi
            
            # Log the error
            echo "Spark job failed with exit code $EXIT_CODE"
            echo "Error output:"
            echo "$OUTPUT"
            
            # Check if we should retry
            if [ $i -le $MAX_RETRIES ]; then
                echo "Retrying in $RETRY_DELAY seconds... (attempt $((i + 1)) of $((MAX_RETRIES + 1)))"
                sleep $RETRY_DELAY
                # Increase delay for next retry (exponential backoff)
                RETRY_DELAY=$((RETRY_DELAY * 2))
            fi
        done
        
        # If we get here, all retries failed
        echo "Spark job failed after $((MAX_RETRIES + 1)) attempts"
        exit 1
    else
        echo "Error: transform.py not found at /opt/airflow/dags/spark/transform.py"
        echo "Contents of /opt/airflow/dags/:"
        ls -la /opt/airflow/dags/
        exit 1
    fi
    ''',
    dag=dag,
    retries=2,  # Número de retentativas no nível do Airflow
    retry_delay=timedelta(minutes=10),  # Tempo entre as retentativas do Airflow
    retry_exponential_backoff=True,  # Habilita backoff exponencial
    max_retry_delay=timedelta(minutes=30),  # Tempo máximo de espera entre tentativas
    execution_timeout=timedelta(minutes=30),  # Tempo máximo de execução da tarefa
)

run_java_client >> run_spark_transform
