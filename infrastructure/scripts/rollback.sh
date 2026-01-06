#!/bin/bash
# Rollback Script
# Rollback به نسخه قبلی

set -e

ENVIRONMENT=${1:-staging}

echo "Rolling back $ENVIRONMENT environment..."

# Get previous version
PREVIOUS_VERSION=$(docker images --format "{{.Tag}}" | grep -v latest | sort -V | tail -n 1)

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "No previous version found"
    exit 1
fi

echo "Rolling back to version: $PREVIOUS_VERSION"

# Update docker-compose to use previous version
# This is a placeholder - actual implementation depends on your setup

# Example:
# sed -i "s/:latest/:$PREVIOUS_VERSION/g" docker-compose.yml
# docker-compose up -d

echo "Rollback completed to version: $PREVIOUS_VERSION"

