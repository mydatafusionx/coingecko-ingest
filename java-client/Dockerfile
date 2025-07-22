# Build stage
FROM maven:3.9.6-eclipse-temurin-21 AS builder

# Cria e define o diretório de trabalho
WORKDIR /build

# Copia os arquivos do projeto
COPY java-client/pom.xml .
COPY java-client/src ./src

# Baixa as dependências e compila
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:21-jre
WORKDIR /app

# Copia o JAR gerado
COPY --from=builder /build/target/coin-gecko-ingest-*.jar app.jar

ENTRYPOINT ["java", "-jar", "app.jar"]
