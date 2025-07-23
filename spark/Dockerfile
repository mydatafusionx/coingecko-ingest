FROM bitnami/spark:3.4.1

# Instalar as dependências do Python
USER root

# Atualizar o pip e instalar as dependências do sistema
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install --upgrade pip && \
    pip3 install --upgrade setuptools

# Copiar e instalar os requisitos do Python
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Instalar o py4j com a versão correta para o PySpark 3.4.1
RUN pip3 install py4j==0.10.9.7

# Criar diretório de trabalho e copiar o script
RUN mkdir -p /app
COPY transform.py /app/transform.py

# Configurar o diretório de trabalho e usuário
WORKDIR /app
USER 1001
