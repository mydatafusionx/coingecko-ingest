# Build stage
FROM maven:3.9.6-eclipse-temurin-21 AS builder

# Cria e define o diretório de trabalho
WORKDIR /app

# Copia o pom.xml primeiro para aproveitar o cache do Docker
COPY java-client/pom.xml .

# Baixa as dependências
RUN mvn dependency:go-offline

# Copia o código-fonte
COPY java-client/src ./src

# Compila o projeto e gera o JAR com um nome específico
RUN mvn clean package -DskipTests && \
    cp /app/target/coin-gecko-ingest-1.0-SNAPSHOT.jar /app/target/app.jar

# Runtime stage
FROM eclipse-temurin:21-jre
WORKDIR /app

# Cria o diretório de dados
RUN mkdir -p /data/raw

# Copia o JAR gerado
COPY --from=builder /app/target/app.jar .

ENTRYPOINT ["java", "-jar", "app.jar"]
