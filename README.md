# DataFusion Ingest – API Delta Pipeline

## 🎯 Objetivo
Pipeline batch que consome dados da API CoinGecko, transforma com PySpark e armazena em Delta Lake. Orquestração via Airflow, monitoramento com Prometheus/Grafana, CI/CD e deploy automatizado.

## 🚀 Pré-requisitos

### Para execução local
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ de RAM recomendado
- 10GB+ de espaço em disco

### Para deploy em produção (VPS/EC2)
- Ubuntu 20.04/22.04 LTS
- Docker e Docker Compose instalados
- 4GB+ de RAM (8GB recomendado)
- 20GB+ de espaço em disco
- Portas 80, 443, 8080, 3000, 9090 liberadas

## 🖥️ Execução Local

1. **Clone o repositório**
   ```bash
   git clone https://github.com/mydatafusionx/coingecko-ingest.git
   cd coingecko-ingest
   ```

2. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env conforme necessário
   ```

3. **Inicie os containers**
   ```bash
   docker-compose up --build -d
   ```

4. **Acesse os serviços**
   - Airflow: http://localhost:8080 (usuário: `airflow`, senha: `airflow`)
   - Spark UI: http://localhost:4040
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (usuário: `admin`, senha: `admin`)

## ☁️ Deploy em Produção (VPS/EC2)

### 1. Configuração Inicial do Servidor

```bash
# Atualize o sistema
sudo apt update && sudo apt upgrade -y

# Instale pré-requisitos
sudo apt install -y git docker.io docker-compose

# Adicione seu usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Implantação Manual

```bash
# Clone o repositório
mkdir -p /opt/coingecko-ingest
cd /opt/coingecko-ingest
git clone https://github.com/mydatafusionx/coingecko-ingest.git .

# Configure as variáveis de ambiente
cp .env.example .env
nano .env  # Edite conforme necessário

# Crie diretórios de dados
mkdir -p data/raw data/delta

# Inicie os containers
docker-compose up --build -d
```

### 3. Configuração do Nginx (Opcional, para HTTPS)

```bash
# Instale o Nginx
sudo apt install -y nginx

# Configure o proxy reverso
sudo nano /etc/nginx/sites-available/coingecko
```

Adicione a configuração do Nginx (substitua `SEU_DOMINIO`):

```nginx
server {
    listen 80;
    server_name SEU_DOMINIO;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Ative o site e recarregue o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/coingecko /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Atualização Automática (CI/CD)

1. **Configure as secrets no GitHub** (Settings > Secrets > Actions):
   - `DEPLOY_HOST`: Endereço do seu servidor
   - `DEPLOY_USER`: Usuário SSH
   - `DEPLOY_KEY`: Chave privada SSH

2. **Ative o workflow de CI/CD**
   - O workflow já está configurado no repositório
   - Push na branch `main` dispara o deploy automático

## 🔧 Estrutura do Projeto

```
.
├── airflow/               # Configurações do Airflow
│   ├── dags/             # DAGs do Airflow
│   ├── Dockerfile        # Imagem personalizada
│   └── requirements.txt  # Dependências Python
├── java-client/          # Cliente Java para API CoinGecko
├── spark/                # Scripts PySpark
│   └── transform.py      # Transformação de dados
├── monitoring/           # Configurações de monitoramento
│   ├── prometheus/       # Configuração do Prometheus
│   └── grafana/          # Dashboards e configurações
├── data/                 # Dados (não versionado)
│   ├── raw/             # Dados brutos da API
│   └── delta/           # Dados processados (Delta Lake)
├── docker-compose.yml    # Orquestração de containers
└── README.md            # Este arquivo
```

## 🔄 Fluxo de Dados

1. **Extração**: Cliente Java consome a API CoinGecko
2. **Armazenamento Bruto**: Dados salvos em JSON no diretório `data/raw`
3. **Transformação**: PySpark processa e converte para Delta Lake
4. **Armazenamento**: Dados estruturados em Delta Lake (`data/delta`)
5. **Monitoramento**: Métricas coletadas pelo Prometheus e visualizadas no Grafana

## 🔍 Acesso aos Dados

Os dados processados estão disponíveis em `data/delta/` no formato Delta Lake. Para acessá-los:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("DeltaRead") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

df = spark.read.format("delta").load("data/delta/market_prices")
df.show()
```

## 📊 Monitoramento com Grafana

O Grafana é uma ferramenta poderosa para visualização de métricas e logs. Neste projeto, ele é pré-configurado para monitorar o Airflow, Spark e métricas do sistema.

### Acessando o Grafana

1. **Localmente**: Acesse http://localhost:3000
2. **Em produção**: Acesse `http://seu-dominio:3000` (ou a porta configurada)

**Credenciais padrão**:
- Usuário: `admin`
- Senha: `admin` (será solicitado alteração no primeiro acesso)

### Configurando Fontes de Dados

1. **Prometheus** (já pré-configurado):
   - Nome: `Prometheus`
   - URL: `http://prometheus:9090`
   - Access: `Server`

2. **Loki** (para logs, se configurado):
   - Nome: `Loki`
   - URL: `http://loki:3100`
   - Access: `Server`

### Dashboards Importantes

1. **Airflow Metrics**
   - Monitora execução de DAGs e tarefas
   - Métricas de sucesso/falha
   - Tempo de execução das tarefas

2. **Spark Monitoring**
   - Uso de recursos (CPU, memória)
   - Execução de jobs e estágios
   - Throughput de processamento

3. **System Metrics**
   - Uso de CPU, memória e disco
   - Rede e E/S
   - Uso de containers Docker

### Criando um Novo Dashboard

1. Clique em "+" > "Create" > "Dashboard"
2. Adicione um novo painel clicando em "Add panel"
3. Selecione a fonte de dados (ex: Prometheus)
4. Use PromQL para criar suas consultas, por exemplo:
   ```
   # Taxa de sucesso das DAGs
   rate(airflow_dagrun_duration_success[5m])
   
   # Uso de memória do Spark
   jvm_memory_bytes_used{container_label_com_docker_compose_service="spark-worker"}
   ```
5. Personalize a visualização (gráfico, tabela, etc.)

### Alertas no Grafana

1. Vá em "Alert" > "Alert rules" > "New alert rule"
2. Defina a condição de alerta (ex: memória > 90% por 5 minutos)
3. Configure os canais de notificação (Email, Slack, etc.)

### Dicas de Uso

- Use variáveis de dashboard para criar filtros reutilizáveis
- Exporte/importe dashboards para backup ou compartilhamento
- Configure permissões de usuário para controle de acesso

## 📊 Outras Ferramentas de Monitoramento

- **Airflow UI**: Monitoramento de DAGs e tarefas
- **Prometheus**: Consulta detalhada de métricas
- **Spark UI**: Monitoramento de jobs Spark
- **Grafana Logs**: Visualização centralizada de logs

## 🔄 Manutenção

### Atualizando o Projeto

```bash
# No servidor de produção
cd /opt/coingecko-ingest
git pull
docker-compose up --build -d
```

### Limpando Dados Antigos

```bash
# Limpar dados antigos (cuidado!)
docker-compose down -v
```

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia nosso [guia de contribuição](CONTRIBUTING.md) para detalhes sobre como enviar pull requests.

---

Desenvolvido por [Seu Nome] - [Seu Site] - [Seu Email]
