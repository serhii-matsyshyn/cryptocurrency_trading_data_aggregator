#!/bin/bash

sudo docker-compose -f docker-compose-infrastructure.yml up -d

# Function to check if Cassandra service is healthy
function is_cassandra_healthy() {
    HEALTH=$(docker-compose -f docker-compose-infrastructure.yml ps -q cassandra1)
    if [ -n "$HEALTH" ]; then
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$HEALTH")
        echo "Cassandra health status: $HEALTH_STATUS"
        if [ "$HEALTH_STATUS" == "healthy" ]; then
            return 0
        fi
    fi
    return 1
}

# Wait for Cassandra service to be healthy
until is_cassandra_healthy; do
    echo "Waiting for Cassandra to be healthy..."
    sleep 5
done

sleep 15

# Execute the desired command
cat schema_creation.cql | sudo docker exec -i cassandra1 cqlsh
python3 import_yaml_to_consul.py
