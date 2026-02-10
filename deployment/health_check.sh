#!/bin/bash

# Health check script
# Can be used for monitoring or load balancer health checks

set -e

# Check if Django is responding
if curl -f -s http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✓ Django is healthy"
    exit 0
else
    echo "✗ Django is not responding"
    exit 1
fi
