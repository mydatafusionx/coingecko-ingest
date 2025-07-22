FROM apache/airflow:2.8.1-python3.10

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories and set permissions
RUN mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins \
    && chown -R airflow:0 /opt/airflow \
    && chmod -R 775 /opt/airflow/logs \
    && chmod -R 775 /opt/airflow/dags \
    && chmod g+rwx /opt/airflow

# Copy DAGs and requirements
COPY --chown=airflow:0 dags/ /opt/airflow/dags/
COPY --chown=airflow:0 requirements.txt /tmp/requirements.txt

# Switch to airflow user for Python package installation
USER airflow
WORKDIR /opt/airflow

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install required providers
RUN pip install --no-cache-dir \
    apache-airflow-providers-docker \
    apache-airflow-providers-apache-spark

# Add user's local bin to PATH
ENV PATH="/home/airflow/.local/bin:${PATH}"

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__FERNET_KEY=
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
ENV AIRFLOW__CORE__STORE_SERIALIZED_DAGS=true
ENV AIRFLOW__WEBSERVER__WORKER_REFRESH_INTERVAL=3600

# Ensure the entrypoint script is executable
USER root
COPY --chown=airflow:0 entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER airflow

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["webserver"]
