#!/bin/bash
set -e

# Atualizar o sistema
echo "🔄 Atualizando o sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# Instalar dependências
echo "📦 Instalando dependências..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    docker.io \
    docker-compose

# Configurar Docker
echo "🐳 Configurando Docker..."
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Criar diretórios de dados
echo "📂 Criando diretórios..."
sudo mkdir -p /opt/coingecko-ingest/data/{raw,delta,processed}
sudo chown -R $USER:$USER /opt/coingecko-ingest
sudo chmod -R 777 /opt/coingecko-ingest/data

echo "✅ Configuração inicial concluída!"
echo "Próximos passos:"
echo "1. Adicione suas variáveis de ambiente no arquivo .env"
echo "2. Execute 'docker-compose up -d' para iniciar os serviços"
