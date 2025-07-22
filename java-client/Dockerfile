# Etapa de build
FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /build
# Copia apenas o POM primeiro para aproveitar o cache do Docker
COPY pom.xml .
# Baixa as dependências (cacheado enquanto o POM não mudar)
RUN mvn dependency:go-offline
# Copia o código fonte
COPY src/ /build/src/
# Compila o projeto
RUN mvn clean package -DskipTests

# Etapa de execução
FROM eclipse-temurin:21-jdk
WORKDIR /app
# Copia apenas o JAR gerado
COPY --from=build /build/target/coin-gecko-ingest-*.jar /app/coin-gecko-ingest.jar

# Configura o entrypoint
ENTRYPOINT ["java", "-jar", "coin-gecko-ingest.jar"]
