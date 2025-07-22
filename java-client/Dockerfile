FROM eclipse-temurin:21-jdk
WORKDIR /app

# Copia o JAR do diretório local para o container
COPY docker-java-target/coin-gecko-ingest.jar /app/coin-gecko-ingest.jar

ENTRYPOINT ["java", "-jar", "coin-gecko-ingest.jar"]
