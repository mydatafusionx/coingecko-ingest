#!/usr/bin/env bash
set -e

# Initialize the database if not already done
if [ "$1" = "webserver" ]; then
    # Wait for the database to be ready
    until airflow db check; do
        echo "Waiting for database to be ready..."
        sleep 5
    done

    # Initialize the database if needed
    if [ ! -f "${AIRFLOW_HOME}/airflow.db" ]; then
        echo "Initializing Airflow database..."
        airflow db init
        
        echo "Creating admin user..."
        airflow users create \
            --username admin \
            --password admin \
            --firstname Admin \
            --lastname User \
            --role Admin \
            --email admin@example.org
    fi
    
    # Upgrade the database to the latest version
    airflow db upgrade
fi

# Execute the command passed to the container
exec airflow "$@"
