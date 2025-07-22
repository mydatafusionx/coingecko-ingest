FROM apache/airflow:2.8.1-python3.10

USER root

# Instala o provider Docker como usuário airflow
USER airflow
RUN pip install --user apache-airflow-providers-docker

# Volta para root para copiar arquivos
USER root

# Copia os DAGs para o diretório correto
COPY --chown=airflow:0 dags/ /opt/airflow/dags/

# Define o usuário padrão
USER 50000
