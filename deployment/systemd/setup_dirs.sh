#!/bin/bash

# Script to create necessary directories and set permissions
# Run this before starting services

# Create log directories
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/log/daphne
sudo mkdir -p /var/log/celery

# Create run directories for PID files
sudo mkdir -p /var/run/celery

# Set ownership to ubuntu user
sudo chown -R ubuntu:ubuntu /var/log/gunicorn
sudo chown -R ubuntu:ubuntu /var/log/daphne
sudo chown -R ubuntu:ubuntu /var/log/celery
sudo chown -R ubuntu:ubuntu /var/run/celery

# Set permissions
sudo chmod -R 755 /var/log/gunicorn
sudo chmod -R 755 /var/log/daphne
sudo chmod -R 755 /var/log/celery
sudo chmod -R 755 /var/run/celery

echo "✓ Directories and permissions configured"
