# Build stage
FROM maven:3.9.6-eclipse-temurin-21 AS builder

# Cria e define o diretório de trabalho
WORKDIR /build

# Verifica os arquivos no diretório atual
RUN pwd && ls -la

# Copia o pom.xml primeiro para aproveitar o cache do Docker
COPY pom.xml .

# Verifica se o pom.xml foi copiado
RUN ls -la pom.xml

# Copia o diretório src
COPY src/ /build/src/

# Verifica a estrutura do diretório src
RUN find /build/src -type f

# Baixa as dependências e compila
RUN mvn clean package -DskipTests

# Verifica se o JAR foi gerado
RUN ls -la /build/target/

# Runtime stage
FROM eclipse-temurin:21-jre
WORKDIR /app

# Copia o JAR gerado
COPY --from=builder /build/target/coin-gecko-ingest-*.jar app.jar

# Verifica se o JAR foi copiado
RUN ls -la /app/

ENTRYPOINT ["java", "-jar", "app.jar"]
