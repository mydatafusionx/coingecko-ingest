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
    echo "Contents of /opt/airflow/spark:"
    ls -la /opt/airflow/spark/ || echo "Failed to list spark directory"
    
    # Copy the transform.py script to the spark-master container
    if [ -f "/opt/airflow/spark/transform.py" ]; then
        echo "Copying transform.py to spark-master container..."
        docker cp /opt/airflow/spark/transform.py spark-master:/tmp/transform.py
        
        # Verify the file was copied
        echo "Verifying file was copied to spark-master container:"
        docker exec spark-master ls -la /tmp/transform.py || echo "File not found in container"
        
        # Run the Spark job
        echo "Running Spark job..."
        docker exec spark-master spark-submit \
            --packages io.delta:delta-core_2.12:2.4.0 \
            --conf 'spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension' \
            --conf 'spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog' \
            /tmp/transform.py
    else
        echo "Error: transform.py not found at /opt/airflow/spark/transform.py"
        echo "Contents of /opt/airflow:"
        ls -la /opt/airflow/
        exit 1
    fi
    ''',
    dag=dag,
)

run_java_client >> run_spark_transform
