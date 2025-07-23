#!/bin/bash

# Stop and remove existing containers
docker-compose down

# Rebuild and start the services
docker-compose up -d --build

echo "Waiting for services to start..."
sleep 30

echo "Services have been restarted with Prometheus monitoring enabled."
echo "Access the following services:"
echo "- Airflow: http://localhost:8081"
echo "- Spark Master: http://localhost:8080"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/admin)"

echo ""
echo "To import the dashboards in Grafana:"
echo "1. Log in to Grafana at http://localhost:3000"
echo "2. Go to Dashboards -> Import"
echo "3. Upload the JSON files from monitoring/grafana/dashboards/"
