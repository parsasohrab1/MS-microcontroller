#!/bin/bash
# Health Check Script
# بررسی سلامت سرویس‌ها

set -e

BASE_URL=$1
TIMEOUT=${2:-30}
MAX_RETRIES=${3:-5}

if [ -z "$BASE_URL" ]; then
    echo "Usage: $0 <base_url> [timeout] [max_retries]"
    exit 1
fi

echo "Checking health of $BASE_URL..."

RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -f -s --max-time $TIMEOUT "$BASE_URL/health" > /dev/null; then
        echo "Health check passed!"
        exit 0
    fi
    
    RETRY=$((RETRY + 1))
    echo "Health check failed. Retry $RETRY/$MAX_RETRIES..."
    sleep 5
done

echo "Health check failed after $MAX_RETRIES retries"
exit 1

