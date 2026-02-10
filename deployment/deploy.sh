#!/bin/bash

# Deployment script for updating the application
# Run this script after pushing changes to git

set -e

echo "=================================="
echo "Deploying RubberEdge Backend"
echo "=================================="

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Navigate to project directory
cd /home/ubuntu/rubberedge/backend

# Pull latest changes
echo "Pulling latest changes from git..."
git pull origin main
print_success "Code updated"

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
print_success "Dependencies updated"

# Run migrations
echo "Running migrations..."
python manage.py migrate
print_success "Migrations completed"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"

# Restart services
echo "Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart daphne
sudo systemctl restart celery
sudo systemctl restart celerybeat
sudo systemctl restart nginx
print_success "Services restarted"

# Check service status
echo ""
echo "Checking service status..."
sleep 2

if sudo systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn is running"
else
    echo "⚠ Gunicorn check: sudo systemctl status gunicorn"
fi

if sudo systemctl is-active --quiet daphne; then
    print_success "Daphne is running"
else
    echo "⚠ Daphne check: sudo systemctl status daphne"
fi

if sudo systemctl is-active --quiet celery; then
    print_success "Celery is running"
else
    echo "⚠ Celery check: sudo systemctl status celery"
fi

echo ""
print_success "Deployment completed!"
echo ""
echo "Useful commands:"
echo "  - View Gunicorn logs: sudo journalctl -u gunicorn -f"
echo "  - View Daphne logs: sudo journalctl -u daphne -f"
echo "  - View Celery logs: sudo journalctl -u celery -f"
