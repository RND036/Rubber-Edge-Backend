# AWS Free Tier Deployment Guide

Complete guide to deploy your Django application on AWS Free Tier.

## 🎯 AWS Free Tier Resources

- **EC2**: 750 hours/month of t2.micro instance (1 vCPU, 1 GB RAM)
- **RDS**: 750 hours/month of db.t2.micro (PostgreSQL)
- **S3**: 5 GB storage for media files
- **Data Transfer**: 15 GB/month outbound
- **EBS**: 30 GB General Purpose SSD

---

## 📋 Prerequisites

1. AWS Account (Free Tier eligible)
2. Domain name (optional, but recommended)
3. SSH key pair for EC2 access
4. Basic knowledge of Linux commands

---

## 🚀 Step-by-Step Deployment

### Step 1: Launch EC2 Instance

1. **Login to AWS Console** → EC2 Dashboard
2. **Launch Instance**:
   - **Name**: rubberedge-backend
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance Type**: t2.micro (1 vCPU, 1 GB RAM)
   - **Key Pair**: Create new or use existing
   - **Network Settings**:
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow HTTPS (port 443) from anywhere
     - Allow Custom TCP (port 8000) for testing
   - **Storage**: 30 GB gp3 (Free tier: 30 GB)

3. **Launch** and wait for instance to start

4. **Note your instance Public IP** (e.g., 3.25.123.45)

### Step 2: Connect to EC2 Instance

```bash
# Download your key pair (e.g., rubberedge-key.pem)
chmod 400 rubberedge-key.pem

# Connect to instance
ssh -i rubberedge-key.pem ubuntu@YOUR-EC2-PUBLIC-IP
```

### Step 3: Setup Server Environment

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y postgresql-client
sudo apt install -y nginx
sudo apt install -y redis-server
sudo apt install -y git
sudo apt install -y supervisor

# Install system dependencies for ML and image processing
sudo apt install -y libpq-dev
sudo apt install -y libjpeg-dev zlib1g-dev
sudo apt install -y python3-opencv

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Step 4: Setup RDS PostgreSQL Database

1. **Go to RDS Dashboard** → Create database
2. **Configuration**:
   - **Engine**: PostgreSQL 15.x
   - **Templates**: Free tier
   - **DB Instance**: db.t2.micro (or db.t3.micro)
   - **DB Instance Identifier**: rubberedge-db
   - **Master Username**: postgres
   - **Master Password**: [Create strong password]
   - **Storage**: 20 GB (Free tier)
   - **Public Access**: Yes (for initial setup)
   - **VPC Security Group**: Create new
     - Add inbound rule: PostgreSQL (5432) from EC2 security group

3. **Note Your RDS Endpoint**: 
   ```
   rubberedge-db.xxxx.us-east-1.rds.amazonaws.com
   ```

4. **Test Connection from EC2**:
   ```bash
   psql -h your-rds-endpoint.rds.amazonaws.com -U postgres -d postgres
   # Enter password when prompted
   
   # Create database
   CREATE DATABASE rubber_db;
   \q
   ```

### Step 5: Setup S3 Bucket for Media Files

1. **Go to S3** → Create bucket
2. **Configuration**:
   - **Bucket Name**: rubberedge-media (must be globally unique)
   - **Region**: Same as EC2 (e.g., us-east-1)
   - **Block all public access**: Uncheck (we'll configure public read for media)
   - **Bucket Versioning**: Disable
   - **Create bucket**

3. **Configure Bucket Policy** (replace YOUR-BUCKET-NAME):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/media/*"
       }
     ]
   }
   ```

4. **Create IAM User for S3 Access**:
   - Go to IAM → Users → Add user
   - Name: rubberedge-s3-user
   - Access type: Programmatic access
   - Attach policy: AmazonS3FullAccess (or create custom policy)
   - **Save Access Key ID and Secret Access Key**

### Step 6: Deploy Application Code

```bash
# On EC2 instance
cd /home/ubuntu

# Clone your repository
git clone https://github.com/YOUR-USERNAME/rubberedge.git
cd rubberedge/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn daphne
pip install boto3 django-storages  # For S3
pip install psycopg2-binary  # PostgreSQL adapter
```

### Step 7: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add the following (replace with your values):

```env
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
AWS_S3_CUSTOM_DOMAIN=rubberedge-media.s3.amazonaws.com

# Twilio (Optional)
TWILIO_ENABLED=False
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Celery
ENABLE_AUTO_SCRAPING=True
```

### Step 8: Run Django Migrations

```bash
# Activate virtual environment
source /home/ubuntu/rubberedge/backend/venv/bin/activate
cd /home/ubuntu/rubberedge/backend

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test if server starts
python manage.py runserver 0.0.0.0:8000
# Press Ctrl+C to stop
```

### Step 9: Setup Systemd Services

The systemd service files are in `deployment/systemd/` folder:

```bash
# Copy service files
sudo cp deployment/systemd/gunicorn.service /etc/systemd/system/
sudo cp deployment/systemd/daphne.service /etc/systemd/system/
sudo cp deployment/systemd/celery.service /etc/systemd/system/
sudo cp deployment/systemd/celerybeat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable gunicorn daphne celery celerybeat
sudo systemctl start gunicorn daphne celery celerybeat

# Check status
sudo systemctl status gunicorn
sudo systemctl status daphne
sudo systemctl status celery
sudo systemctl status celerybeat
```

### Step 10: Configure Nginx

```bash
# Copy Nginx configuration
sudo cp deployment/nginx/rubberedge /etc/nginx/sites-available/

# Update the configuration with your domain/IP
sudo nano /etc/nginx/sites-available/rubberedge

# Enable site
sudo ln -s /etc/nginx/sites-available/rubberedge /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 11: Setup SSL Certificate (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## 🔧 Management Commands

### View Logs

```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Daphne logs (WebSocket)
sudo journalctl -u daphne -f

# Celery logs
sudo journalctl -u celery -f

# Celery Beat logs
sudo journalctl -u celerybeat -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Restart Services

```bash
# After code changes
cd /home/ubuntu/rubberedge/backend
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart daphne
sudo systemctl restart celery
sudo systemctl restart celerybeat
sudo systemctl restart nginx
```

### Database Backup

```bash
# Backup RDS database
pg_dump -h your-rds-endpoint.rds.amazonaws.com -U postgres -d rubber_db > backup.sql

# Restore
psql -h your-rds-endpoint.rds.amazonaws.com -U postgres -d rubber_db < backup.sql
```

---

## 📊 Monitoring

### Check System Resources

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Check running processes
ps aux | grep python
```

### Database Connections

```bash
# Check active connections to RDS
psql -h your-rds-endpoint.rds.amazonaws.com -U postgres -d rubber_db -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 💰 Cost Optimization

1. **Stop EC2 when not in use** (for testing)
2. **Use CloudWatch alarms** to monitor usage
3. **Delete old RDS snapshots**
4. **Use S3 lifecycle policies** to archive old files
5. **Enable RDS Multi-AZ only if needed** (not free)

---

## 🔒 Security Best Practices

1. **Use Security Groups properly**:
   - Restrict SSH to your IP only
   - Use VPC for RDS (not public)
   
2. **Environment Variables**:
   - Never commit `.env` to git
   - Use AWS Secrets Manager for production

3. **Regular Updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

5. **Change Django SECRET_KEY**:
   ```python
   # Generate new key
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

---

## 🐛 Troubleshooting

### Service won't start
```bash
sudo journalctl -u gunicorn -n 50
sudo systemctl status gunicorn
```

### Database connection issues
```bash
# Test from EC2
psql -h your-rds-endpoint.rds.amazonaws.com -U postgres -d rubber_db

# Check security groups
# Ensure RDS security group allows EC2 security group
```

### Static files not loading
```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

### WebSocket connection fails
```bash
sudo systemctl status daphne
sudo journalctl -u daphne -f
# Check Nginx WebSocket configuration
```

### Celery tasks not running
```bash
sudo systemctl status celery celerybeat
sudo journalctl -u celery -f
```

---

## 📱 Mobile App Configuration

Update your mobile app API endpoint to:
```
https://your-domain.com/api/
wss://your-domain.com/ws/
```

Or if using IP:
```
http://your-ec2-ip/api/
ws://your-ec2-ip/ws/
```

---

## 🎓 Free Tier Limits

Monitor your usage to stay within free tier:
- **EC2**: 750 hours/month (1 instance running 24/7)
- **RDS**: 750 hours/month (1 instance running 24/7)
- **S3**: 5 GB storage, 20,000 GET requests
- **Data Transfer**: 15 GB/month outbound

**Tip**: Free tier is valid for **12 months** from AWS account creation.

---

## 📚 Additional Resources

- [AWS Free Tier](https://aws.amazon.com/free/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [RDS User Guide](https://docs.aws.amazon.com/rds/)

---

## ✅ Deployment Checklist

- [ ] EC2 instance launched and accessible
- [ ] RDS PostgreSQL database created
- [ ] S3 bucket created with IAM user
- [ ] Code deployed to EC2
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] Superuser created
- [ ] Static files collected
- [ ] Systemd services running
- [ ] Nginx configured and running
- [ ] SSL certificate installed (optional)
- [ ] Mobile app pointing to new API
- [ ] Test all endpoints
- [ ] Test WebSocket connections
- [ ] Test file uploads (to S3)
- [ ] Monitor logs for errors

---

## 🚨 Important Notes

1. **Free tier expires after 12 months** - Plan ahead!
2. **Monitor billing** - Set up billing alerts in AWS
3. **Backup regularly** - RDS automated backups are free
4. **Security groups** - Always restrict access
5. **Use environment variables** - Never hardcode secrets

---

Need help? Check the troubleshooting section or AWS documentation.
