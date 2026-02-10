# Monitoring Script for AWS Deployment
# Checks status of all services and reports

#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=================================="
echo "RubberEdge Backend - Status Check"
echo "=================================="
echo ""

# Check Gunicorn
if sudo systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✓ Gunicorn is running${NC}"
else
    echo -e "${RED}✗ Gunicorn is not running${NC}"
    echo "  Check logs: sudo journalctl -u gunicorn -n 50"
fi

# Check Daphne
if sudo systemctl is-active --quiet daphne; then
    echo -e "${GREEN}✓ Daphne is running${NC}"
else
    echo -e "${RED}✗ Daphne is not running${NC}"
    echo "  Check logs: sudo journalctl -u daphne -n 50"
fi

# Check Celery
if sudo systemctl is-active --quiet celery; then
    echo -e "${GREEN}✓ Celery is running${NC}"
else
    echo -e "${RED}✗ Celery is not running${NC}"
    echo "  Check logs: sudo journalctl -u celery -n 50"
fi

# Check Celery Beat
if sudo systemctl is-active --quiet celerybeat; then
    echo -e "${GREEN}✓ Celery Beat is running${NC}"
else
    echo -e "${RED}✗ Celery Beat is not running${NC}"
    echo "  Check logs: sudo journalctl -u celerybeat -n 50"
fi

# Check Nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is not running${NC}"
    echo "  Check logs: sudo journalctl -u nginx -n 50"
fi

# Check Redis
if sudo systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running${NC}"
    echo "  Check logs: sudo journalctl -u redis-server -n 50"
fi

echo ""
echo "System Resources:"
echo "=================================="

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${RED}⚠ Disk usage: ${DISK_USAGE}% (High!)${NC}"
else
    echo -e "${GREEN}✓ Disk usage: ${DISK_USAGE}%${NC}"
fi

# Check memory
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 80 ]; then
    echo -e "${RED}⚠ Memory usage: ${MEM_USAGE}% (High!)${NC}"
else
    echo -e "${GREEN}✓ Memory usage: ${MEM_USAGE}%${NC}"
fi

# Check CPU load
CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
echo -e "${NC}→ CPU load: ${CPU_LOAD}${NC}"

echo ""
echo "Recent Errors (Last hour):"
echo "=================================="

# Check for recent errors in logs
ERROR_COUNT=$(sudo journalctl --since "1 hour ago" -p err | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT errors in the last hour${NC}"
    echo "  View errors: sudo journalctl --since '1 hour ago' -p err"
else
    echo -e "${GREEN}✓ No errors in the last hour${NC}"
fi

echo ""
