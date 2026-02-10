#!/bin/bash

# AWS EC2 Setup Script for RubberEdge Backend
# Run this script on your EC2 instance after connecting via SSH

set -e  # Exit on error

echo "=================================="
echo "RubberEdge Backend - AWS Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${NC}→ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run this script as root"
    exit 1
fi

echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System packages updated"

echo ""
echo "Step 2: Installing Python and dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y postgresql-client
sudo apt install -y nginx
sudo apt install -y redis-server
sudo apt install -y git
sudo apt install -y supervisor
print_success "Core packages installed"

echo ""
echo "Step 3: Installing system dependencies..."
sudo apt install -y libpq-dev
sudo apt install -y libjpeg-dev zlib1g-dev
sudo apt install -y python3-opencv
print_success "System dependencies installed"

echo ""
echo "Step 4: Starting Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
print_success "Redis started and enabled"

echo ""
echo "Step 5: Setting up firewall..."
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw --force enable
print_success "Firewall configured"

echo ""
echo "Step 6: Cloning repository..."
print_warning "Please enter your GitHub repository URL:"
read -p "Repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    print_error "Repository URL cannot be empty"
    exit 1
fi

cd /home/ubuntu
if [ -d "rubberedge" ]; then
    print_warning "Directory 'rubberedge' already exists. Skipping clone."
else
    git clone "$REPO_URL" rubberedge
    print_success "Repository cloned"
fi

echo ""
echo "Step 7: Setting up Python virtual environment..."
cd /home/ubuntu/rubberedge/backend
python3 -m venv venv
source venv/bin/activate
print_success "Virtual environment created"

echo ""
echo "Step 8: Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn daphne
pip install boto3 django-storages
pip install psycopg2-binary
print_success "Python packages installed"

echo ""
echo "Step 9: Environment Variables Setup..."
print_warning "You need to configure environment variables manually."
print_info "Edit the .env file: nano /home/ubuntu/rubberedge/backend/.env"
print_info "See AWS_DEPLOYMENT.md for required variables"

if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << 'EOF'
# Django Settings
SECRET_KEY=your-super-secret-key-generate-new-one
DEBUG=False
ALLOWED_HOSTS=your-ec2-public-ip,your-domain.com

# Database (RDS)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rubber_db
DB_USER=postgres
DB_PASSWORD=your-rds-password
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS S3
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_STORAGE_BUCKET_NAME=rubberedge-media
AWS_S3_REGION_NAME=us-east-1

# Twilio (Optional)
TWILIO_ENABLED=False

# Celery
ENABLE_AUTO_SCRAPING=True
EOF
    print_success ".env template created"
    print_warning "IMPORTANT: Edit .env file with your actual values before continuing"
    echo ""
    read -p "Press Enter after configuring .env file..."
fi

echo ""
echo "Step 10: Running Django migrations..."
source venv/bin/activate
python manage.py migrate
print_success "Migrations completed"

echo ""
echo "Step 11: Creating superuser..."
print_info "You'll be prompted to create a superuser account"
python manage.py createsuperuser

echo ""
echo "Step 12: Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"

echo ""
echo "Step 13: Installing systemd services..."
sudo cp deployment/systemd/gunicorn.service /etc/systemd/system/
sudo cp deployment/systemd/daphne.service /etc/systemd/system/
sudo cp deployment/systemd/celery.service /etc/systemd/system/
sudo cp deployment/systemd/celerybeat.service /etc/systemd/system/

sudo systemctl daemon-reload
print_success "Systemd services installed"

echo ""
echo "Step 14: Enabling and starting services..."
sudo systemctl enable gunicorn daphne celery celerybeat
sudo systemctl start gunicorn daphne celery celerybeat
print_success "Services started"

echo ""
echo "Step 15: Checking service status..."
sleep 2
if sudo systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn is running"
else
    print_error "Gunicorn failed to start. Check: sudo journalctl -u gunicorn -n 50"
fi

if sudo systemctl is-active --quiet daphne; then
    print_success "Daphne is running"
else
    print_error "Daphne failed to start. Check: sudo journalctl -u daphne -n 50"
fi

if sudo systemctl is-active --quiet celery; then
    print_success "Celery is running"
else
    print_error "Celery failed to start. Check: sudo journalctl -u celery -n 50"
fi

if sudo systemctl is-active --quiet celerybeat; then
    print_success "Celery Beat is running"
else
    print_error "Celery Beat failed to start. Check: sudo journalctl -u celerybeat -n 50"
fi

echo ""
echo "Step 16: Configuring Nginx..."
sudo cp deployment/nginx/rubberedge /etc/nginx/sites-available/

# Get EC2 public IP
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
print_info "Your EC2 Public IP: $EC2_IP"

# Update Nginx config with IP
sudo sed -i "s/your-domain.com/$EC2_IP/g" /etc/nginx/sites-available/rubberedge

sudo ln -sf /etc/nginx/sites-available/rubberedge /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
if sudo nginx -t; then
    print_success "Nginx configuration is valid"
    sudo systemctl restart nginx
    print_success "Nginx restarted"
else
    print_error "Nginx configuration has errors"
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
print_success "Your application should now be running!"
print_info "Access your API at: http://$EC2_IP/api/"
print_info "Admin panel at: http://$EC2_IP/admin/"
echo ""
print_warning "Next Steps:"
echo "1. Configure your domain DNS (if using domain)"
echo "2. Install SSL certificate: sudo certbot --nginx -d your-domain.com"
echo "3. Update mobile app API endpoint"
echo "4. Test all endpoints"
echo ""
print_info "Useful commands:"
echo "  - View logs: sudo journalctl -u gunicorn -f"
echo "  - Restart services: sudo systemctl restart gunicorn daphne celery"
echo "  - Check status: sudo systemctl status gunicorn"
echo ""
print_warning "Remember to set up AWS billing alerts!"
echo ""
