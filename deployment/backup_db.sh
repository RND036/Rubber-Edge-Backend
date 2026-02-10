# Backup script for AWS RDS database
# Run this script regularly to backup your database

#!/bin/bash

# Configuration
DB_HOST="${DB_HOST:-your-rds-endpoint.rds.amazonaws.com}"
DB_NAME="${DB_NAME:-rubber_db}"
DB_USER="${DB_USER:-postgres}"
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."

# Create backup
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Backup created: $BACKUP_FILE"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    echo "✓ Backup compressed: ${BACKUP_FILE}.gz"
    
    # Optional: Upload to S3 (uncomment if you want to store backups in S3)
    # aws s3 cp "${BACKUP_FILE}.gz" "s3://your-backup-bucket/backups/"
    
    # Delete backups older than 7 days
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
    echo "✓ Old backups cleaned up"
else
    echo "✗ Backup failed"
    exit 1
fi

echo "Backup completed successfully!"
