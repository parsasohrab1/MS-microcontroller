#!/bin/bash
# Switch Traffic Script
# تغییر ترافیک برای Blue-Green Deployment

set -e

COLOR=$1

if [ -z "$COLOR" ] || [ "$COLOR" != "blue" ] && [ "$COLOR" != "green" ]; then
    echo "Usage: $0 <blue|green>"
    exit 1
fi

echo "Switching traffic to $COLOR environment..."

# Update load balancer target group
# This is a placeholder - actual implementation depends on your infrastructure
# For AWS ALB, you would update the target group weights
# For Nginx, you would update the upstream configuration

# Example for AWS:
# aws elbv2 modify-target-group-attributes \
#     --target-group-arn $TARGET_GROUP_ARN \
#     --attributes Key=stickiness.enabled,Value=true

# Example for Nginx:
# sed -i "s/upstream backend {/upstream backend {\n    server ${COLOR}-backend:8000 weight=100;/" /etc/nginx/nginx.conf
# nginx -s reload

echo "Traffic switched to $COLOR"

