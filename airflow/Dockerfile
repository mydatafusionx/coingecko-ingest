FROM apache/airflow:2.8.1-python3.10

USER root

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cria diretórios necessários
RUN mkdir -p /opt/airflow/logs/scheduler \
    && chown -R airflow:0 /opt/airflow/logs \
    && chmod -R 777 /opt/airflow/logs

# Copia os DAGs e requirements
COPY --chown=airflow:0 dags/ /opt/airflow/dags/
COPY --chown=airflow:0 requirements.txt /tmp/requirements.txt

# Muda para o usuário airflow para instalar as dependências
USER airflow

# Instala as dependências do Python
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Instala os providers necessários
RUN pip install --no-cache-dir \
    apache-airflow-providers-docker \
    apache-airflow-providers-apache-spark

# Adiciona o diretório de binários do usuário ao PATH
ENV PATH="${PATH}:/home/airflow/.local/bin"

# Define variáveis de ambiente
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__FERNET_KEY=''
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION='true'
