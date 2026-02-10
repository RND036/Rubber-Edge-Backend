# AWS Deployment Checklist

Use this checklist to ensure you complete all steps for AWS deployment.

## 📋 Pre-Deployment

### AWS Account Setup
- [ ] Create AWS account (or use existing)
- [ ] Verify email address
- [ ] Add payment method (required even for free tier)
- [ ] Enable MFA (Multi-Factor Authentication) for security

### Billing Alerts (Important!)
- [ ] Go to AWS Console → Billing Dashboard
- [ ] Enable "Receive Billing Alerts"
- [ ] Enable "Receive Free Tier Usage Alerts"
- [ ] Create CloudWatch billing alarm ($1, $5, $10 thresholds)

### GitHub/Code Repository
- [ ] Push all code to GitHub/GitLab
- [ ] Create `.env.example` file (✅ Already created)
- [ ] Ensure `.gitignore` excludes `.env` (✅ Already created)
- [ ] Test application locally
- [ ] Commit and push all changes

---

## 🚀 Step 1: Launch EC2 Instance

- [ ] Go to EC2 Dashboard
- [ ] Click "Launch Instance"
- [ ] Name: `rubberedge-backend`
- [ ] AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
- [ ] Instance Type: t2.micro (1 vCPU, 1 GB RAM)
- [ ] Create/select key pair (download `.pem` file)
- [ ] Configure Security Group:
  - [ ] SSH (22) - Your IP only
  - [ ] HTTP (80) - Anywhere
  - [ ] HTTPS (443) - Anywhere
- [ ] Storage: 30 GB gp3
- [ ] Launch instance
- [ ] Note Public IP address: ________________
- [ ] Save key pair file securely

---

## 💾 Step 2: Setup RDS Database

- [ ] Go to RDS Dashboard
- [ ] Click "Create database"
- [ ] Choose PostgreSQL
- [ ] Template: Free tier
- [ ] DB Instance: db.t2.micro (or db.t3.micro)
- [ ] DB Instance Identifier: `rubberedge-db`
- [ ] Master username: `postgres`
- [ ] Master password: ________________ (save securely!)
- [ ] Storage: 20 GB
- [ ] Public Access: Yes (for now)
- [ ] Create new VPC security group
- [ ] Note RDS endpoint: ________________________________
- [ ] Configure security group:
  - [ ] Allow PostgreSQL (5432) from EC2 security group

### Test RDS Connection
- [ ] SSH into EC2
- [ ] Test: `psql -h RDS-ENDPOINT -U postgres -d postgres`
- [ ] Create database: `CREATE DATABASE rubber_db;`

---

## 📦 Step 3: Setup S3 Bucket

- [ ] Go to S3 Console
- [ ] Create bucket
- [ ] Bucket name: `rubberedge-media-[your-unique-suffix]`
- [ ] Region: Same as EC2 (e.g., us-east-1)
- [ ] Uncheck "Block all public access"
- [ ] Create bucket
- [ ] Configure bucket policy (see AWS_DEPLOYMENT.md)
- [ ] Note bucket name: ________________

### Create IAM User for S3
- [ ] Go to IAM → Users
- [ ] Create user: `rubberedge-s3-user`
- [ ] Access type: Programmatic access
- [ ] Attach policy: AmazonS3FullAccess
- [ ] Note Access Key ID: ________________
- [ ] Note Secret Access Key: ________________ (save securely!)

---

## 🔧 Step 4: Connect and Setup EC2

### Connect to EC2
- [ ] `chmod 400 your-key.pem`
- [ ] `ssh -i your-key.pem ubuntu@YOUR-EC2-IP`

### Clone Repository
- [ ] `cd /home/ubuntu`
- [ ] `git clone YOUR-REPO-URL rubberedge`
- [ ] `cd rubberedge/backend`

### Run Automated Setup
- [ ] `chmod +x deployment/*.sh deployment/systemd/*.sh`
- [ ] `./deployment/setup_aws.sh`
- [ ] Follow prompts and wait for completion

---

## ⚙️ Step 5: Configure Environment

### Edit .env File
- [ ] `nano .env` (or use the template created by setup script)
- [ ] Fill in all values:

```env
SECRET_KEY=[Generate new one!]
DEBUG=False
ALLOWED_HOSTS=[EC2-IP or domain]

DB_NAME=rubber_db
DB_USER=postgres
DB_PASSWORD=[RDS password]
DB_HOST=[RDS endpoint]
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0
USE_REDIS_CHANNELS=True

USE_S3=True
AWS_ACCESS_KEY_ID=[From IAM user]
AWS_SECRET_ACCESS_KEY=[From IAM user]
AWS_STORAGE_BUCKET_NAME=[Your S3 bucket]
AWS_S3_REGION_NAME=[Your region]
```

### Generate Secret Key
- [ ] Run: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- [ ] Copy key to .env

### Save and Exit
- [ ] Save .env file
- [ ] Verify: `cat .env` (check all values are correct)

---

## 🏃 Step 6: Run Django Setup

### Activate Virtual Environment
- [ ] `source venv/bin/activate`

### Run Migrations
- [ ] `python manage.py migrate`
- [ ] Verify: No errors

### Create Superuser
- [ ] `python manage.py createsuperuser`
- [ ] Username: ________________
- [ ] Email: ________________
- [ ] Password: ________________

### Collect Static Files
- [ ] `python manage.py collectstatic --noinput`
- [ ] Verify: Static files collected

---

## 🎯 Step 7: Setup Services

### Create Log Directories
- [ ] `./deployment/systemd/setup_dirs.sh`

### Install Systemd Services
- [ ] `sudo cp deployment/systemd/*.service /etc/systemd/system/`
- [ ] `sudo systemctl daemon-reload`

### Enable Services
- [ ] `sudo systemctl enable gunicorn daphne celery celerybeat`

### Start Services
- [ ] `sudo systemctl start gunicorn daphne celery celerybeat`

### Verify Services
- [ ] `sudo systemctl status gunicorn` - Running?
- [ ] `sudo systemctl status daphne` - Running?
- [ ] `sudo systemctl status celery` - Running?
- [ ] `sudo systemctl status celerybeat` - Running?

---

## 🌐 Step 8: Configure Nginx

### Install Nginx Config
- [ ] `sudo cp deployment/nginx/rubberedge /etc/nginx/sites-available/`

### Update Domain/IP
- [ ] `sudo nano /etc/nginx/sites-available/rubberedge`
- [ ] Replace `your-domain.com` with your EC2 IP or domain
- [ ] Save and exit

### Enable Site
- [ ] `sudo ln -s /etc/nginx/sites-available/rubberedge /etc/nginx/sites-enabled/`
- [ ] `sudo rm /etc/nginx/sites-enabled/default`

### Test and Restart
- [ ] `sudo nginx -t` - Configuration OK?
- [ ] `sudo systemctl restart nginx`

---

## ✅ Step 9: Test Deployment

### Health Check
- [ ] Visit: `http://YOUR-EC2-IP/health/`
- [ ] Should return: `{"status":"healthy","service":"rubberedge-backend"}`

### Admin Panel
- [ ] Visit: `http://YOUR-EC2-IP/admin/`
- [ ] Login with superuser credentials
- [ ] Admin panel loads correctly?

### API Endpoints
- [ ] Test: `curl http://YOUR-EC2-IP/api/`
- [ ] APIs responding?

### WebSocket Connection
- [ ] Test WebSocket connections
- [ ] Chat features working?

### File Upload (S3)
- [ ] Test image/file upload
- [ ] Files appearing in S3 bucket?

### Background Tasks
- [ ] Check Celery tasks running
- [ ] `celery -A rubber_farm_api inspect active`

---

## 🔒 Step 10: SSL Certificate (Optional but Recommended)

### Install Certbot
- [ ] `sudo apt install -y certbot python3-certbot-nginx`

### Get Certificate
- [ ] `sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com`
- [ ] Follow prompts
- [ ] Test auto-renewal: `sudo certbot renew --dry-run`

### Update Mobile App
- [ ] Update API endpoint to `https://yourdomain.com/api/`
- [ ] Update WebSocket to `wss://yourdomain.com/ws/`

---

## 📱 Step 11: Mobile App Configuration

### Update API Endpoints
- [ ] HTTP API: `http://YOUR-IP-OR-DOMAIN/api/`
- [ ] HTTPS API: `https://YOUR-DOMAIN/api/` (if SSL configured)
- [ ] WebSocket: `ws://YOUR-IP-OR-DOMAIN/ws/` or `wss://YOUR-DOMAIN/ws/`

### Test from Mobile App
- [ ] Login works
- [ ] API calls successful
- [ ] WebSocket connections work
- [ ] File uploads work
- [ ] All features functional

---

## 📊 Step 12: Monitoring Setup

### Setup Monitoring Script
- [ ] Test: `./deployment/monitor.sh`
- [ ] All services green?

### Setup Database Backup
- [ ] Configure: `nano deployment/backup_db.sh`
- [ ] Add DB credentials
- [ ] Test: `./deployment/backup_db.sh`
- [ ] Schedule with cron (optional)

### Create Backup Cron Job (Optional)
```bash
# Daily backup at 2 AM
0 2 * * * /home/ubuntu/rubberedge/backend/deployment/backup_db.sh
```

---

## 🎓 Post-Deployment

### Security
- [ ] Change default SSH port (optional)
- [ ] Setup fail2ban (optional)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Monitor CloudWatch metrics

### Documentation
- [ ] Document server IP/domain
- [ ] Save all credentials securely
- [ ] Share API documentation with team
- [ ] Document deployment process for team

### Maintenance
- [ ] Schedule regular backups
- [ ] Monitor disk space
- [ ] Monitor billing dashboard
- [ ] Keep Django/packages updated
- [ ] Review logs regularly

---

## 🐛 Troubleshooting

If something doesn't work:

1. **Check Logs**:
   ```bash
   sudo journalctl -u gunicorn -f
   sudo journalctl -u daphne -f
   sudo journalctl -u celery -f
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Run Monitor Script**:
   ```bash
   ./deployment/monitor.sh
   ```

3. **Restart Services**:
   ```bash
   sudo systemctl restart gunicorn daphne celery celerybeat nginx
   ```

4. **Check Documentation**:
   - [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)
   - Troubleshooting section

---

## 💰 Cost Management

- [ ] Billing alerts configured
- [ ] CloudWatch alarms set up
- [ ] Review usage weekly
- [ ] Delete unused resources
- [ ] Check AWS Cost Explorer monthly

---

## 📝 Notes

Date Deployed: ________________

EC2 IP: ________________

Domain: ________________

Issues Encountered:
1. 
2. 
3. 

Resolution:
1. 
2. 
3. 

---

## ✨ Deployment Complete!

Congratulations! Your RubberEdge backend is now live on AWS! 🎉

**Next Steps:**
1. Monitor for 24-48 hours
2. Test all features thoroughly
3. Share with users/team
4. Set up regular backups
5. Plan for free tier expiration (12 months)

**Support:** Check [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for detailed instructions and troubleshooting.
