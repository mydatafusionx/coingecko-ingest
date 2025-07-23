FROM python:3.10-slim-bullseye

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW_VERSION=2.8.1
ENV PYTHON_VERSION=3.10
ENV DOCKER_VERSION=20.10.23
ENV CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Install system dependencies and create airflow user
RUN set -ex \
    && buildDeps='freetds-dev libkrb5-dev libsasl2-dev libssl-dev libffi-dev libpq-dev git' \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        $buildDeps \
        freetds-bin \
        build-essential \
        default-libmysqlclient-dev \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
    # Install Docker CLI
    && curl -fsSL https://download.docker.com/linux/static/stable/$(uname -m)/docker-${DOCKER_VERSION}.tgz -o docker.tgz \
    && tar xzvf docker.tgz --strip 1 -C /usr/local/bin docker/docker \
    && rm docker.tgz \
    && chmod +x /usr/local/bin/docker \
    && rm -rf /var/lib/apt/lists/*

# Create airflow user and set up directories
RUN useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow \
    && mkdir -p ${AIRFLOW_HOME}/dags \
    && mkdir -p ${AIRFLOW_HOME}/logs \
    && mkdir -p ${AIRFLOW_HOME}/plugins \
    && chown -R airflow:0 ${AIRFLOW_HOME} \
    && chmod -R 775 ${AIRFLOW_HOME}/logs \
    && chmod -R 775 ${AIRFLOW_HOME}/dags \
    && chmod g+rwx ${AIRFLOW_HOME}

# Copy requirements first to leverage Docker cache
COPY --chown=airflow:0 requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "apache-airflow[postgres,celery,redis,ssh,docker]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}" \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir prometheus-client==0.20.0

# Copy necessary files
COPY --chown=airflow:0 dags/ ${AIRFLOW_HOME}/dags/
COPY --chown=airflow:0 entrypoint.sh /entrypoint.sh

# Set the working directory
WORKDIR ${AIRFLOW_HOME}

# Set environment variables
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__FERNET_KEY=''
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
ENV AIRFLOW__CORE__STORE_SERIALIZED_DAGS=true
ENV AIRFLOW__WEBSERVER__WORKER_REFRESH_INTERVAL=3600
ENV PYTHONPATH="${AIRFLOW_HOME}"

# Ensure the entrypoint script is executable
RUN chmod +x /entrypoint.sh

# Switch to airflow user
USER airflow

# Expose the default Airflow port
EXPOSE 8080

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command to run
CMD ["webserver"]
