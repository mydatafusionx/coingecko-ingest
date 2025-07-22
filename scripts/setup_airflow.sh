#!/bin/bash

# Exit on error
set -e

# Create necessary directories
mkdir -p airflow/dags airflow/logs airflow/plugins
mkdir -p data/raw data/delta data/processed

# Set permissions
chmod -R 775 airflow/
chmod -R 775 data/

# Initialize the database
docker-compose up -d postgres
sleep 10  # Wait for PostgreSQL to be ready

# Initialize Airflow metadata database
docker-compose run --rm airflow-webserver airflow db init

# Create admin user
docker-compose run --rm airflow-webserver airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start all services
docker-compose up -d

echo "Airflow setup complete! Access the web UI at http://localhost:8081"
echo "Username: admin"
echo "Password: admin"
