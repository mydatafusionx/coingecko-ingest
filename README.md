# DataFusion Ingest – API Delta Pipeline

## Objetivo
Pipeline batch que consome dados da API CoinGecko, transforma com PySpark e armazena em Delta Lake. Orquestração via Airflow, monitoramento com Prometheus/Grafana, CI/CD e deploy automatizado via SSH (Hostinger).

## Execução Local
```bash
docker-compose up --build
```

## Deploy na Hostinger via CI/CD
1. Configure as secrets no GitHub:
   - HOSTINGER_HOST
   - HOSTINGER_USER
   - SSH_PRIVATE_KEY
2. Push na branch `main` faz o deploy automático via SSH usando Docker Compose.

## Serviços
- Airflow: http://localhost:8080
- Spark UI: http://localhost:4040
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Estrutura
- `/airflow` – DAGs e Dockerfile do Airflow
- `/java-client` – Cliente Java (OkHttp)
- `/spark` – PySpark + Delta Lake
- `/monitoring` – Prometheus/Grafana configs
- `/data/raw` – Dados brutos
- `/data/delta` – Dados Delta Lake

---

> Projeto pronto para rodar localmente e deploy automatizado em VPC via SSH.
