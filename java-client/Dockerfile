# Build stage
FROM maven:3.9.6-eclipse-temurin-21 AS builder

# Cria e define o diretório de trabalho
WORKDIR /app

# Copia primeiro o pom.xml para aproveitar o cache do Docker
COPY pom.xml .

# Baixa as dependências (cacheado enquanto o pom.xml não mudar)
RUN mvn dependency:go-offline

# Cria a estrutura de diretórios
RUN mkdir -p src/main/java

# Copia o código fonte
COPY src/ ./src/

# Build da aplicação
RUN mvn clean package -DskipTests && \
    cp /app/target/coin-gecko-ingest-1.0-SNAPSHOT.jar /app/target/app.jar

# Runtime stage
FROM eclipse-temurin:21-jre
WORKDIR /app

# Cria usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Cria o diretório de dados e ajusta permissões
RUN mkdir -p /data/raw && \
    chown -R appuser:appuser /app /data

# Muda para o usuário não-root
USER appuser

# Copia o JAR gerado
COPY --from=builder --chown=appuser:appuser /app/target/app.jar .

# Define variáveis de ambiente
ENV JAVA_OPTS="-Xms512m -Xmx1024m"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
