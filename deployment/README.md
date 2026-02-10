# AWS Deployment - README

This directory contains all the configuration files and scripts needed to deploy the RubberEdge backend on AWS Free Tier.

## 📁 Directory Structure

```
deployment/
├── AWS_DEPLOYMENT.md          # Main deployment guide
├── AWS_FREE_TIER_GUIDE.md     # Free tier limits and cost optimization
├── setup_aws.sh               # Automated setup script
├── deploy.sh                  # Update/deployment script
├── monitor.sh                 # Service monitoring script
├── backup_db.sh               # Database backup script
├── health_check.sh            # Health check script
├── requirements-aws.txt       # AWS-specific Python packages
├── nginx/
│   └── rubberedge            # Nginx configuration
└── systemd/
    ├── gunicorn.service      # Gunicorn systemd service
    ├── daphne.service        # Daphne (WebSocket) service
    ├── celery.service        # Celery worker service
    ├── celerybeat.service    # Celery beat scheduler service
    └── setup_dirs.sh         # Directory setup script
```

## 🚀 Quick Start

### 1. Launch AWS Resources

1. **EC2 Instance**: t2.micro, Ubuntu 22.04 LTS
2. **RDS PostgreSQL**: db.t2.micro, 20 GB
3. **S3 Bucket**: For media file storage
4. **IAM User**: For S3 access

See [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) for detailed instructions.

### 2. Connect to EC2

```bash
ssh -i your-key.pem ubuntu@YOUR-EC2-IP
```

### 3. Run Setup Script

```bash
# Clone your repository first
git clone https://github.com/YOUR-USERNAME/rubberedge.git
cd rubberedge/backend

# Make scripts executable
chmod +x deployment/*.sh
chmod +x deployment/systemd/*.sh

# Run setup
./deployment/setup_aws.sh
```

### 4. Configure Environment

```bash
# Copy and edit environment variables
cp .env.example .env
nano .env
```

Fill in your:
- Database credentials (RDS)
- AWS S3 credentials
- Secret key
- Domain/IP

### 5. Verify Deployment

```bash
# Check all services
./deployment/monitor.sh

# View logs
sudo journalctl -u gunicorn -f
sudo journalctl -u daphne -f
```

## 📝 Common Tasks

### Deploy Updates

```bash
./deployment/deploy.sh
```

### Check Service Status

```bash
./deployment/monitor.sh
```

### Backup Database

```bash
./deployment/backup_db.sh
```

### Restart Services

```bash
sudo systemctl restart gunicorn daphne celery celerybeat nginx
```

### View Logs

```bash
# Gunicorn (HTTP)
sudo journalctl -u gunicorn -f

# Daphne (WebSocket)
sudo journalctl -u daphne -f

# Celery (Background tasks)
sudo journalctl -u celery -f

# Nginx (Web server)
sudo tail -f /var/log/nginx/rubberedge_error.log
```

## 🔧 Customization

### Update Domain

1. Edit Nginx config:
   ```bash
   sudo nano /etc/nginx/sites-available/rubberedge
   ```

2. Replace `your-domain.com` with your actual domain

3. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

### SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Adjust Workers

Edit systemd service files to change number of workers:

```bash
sudo nano /etc/systemd/system/gunicorn.service
# Change --workers 3 to desired number

sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

## 📊 Monitoring

### System Resources

```bash
# CPU and Memory
htop

# Disk space
df -h

# Network
netstat -tulpn
```

### Application Metrics

```bash
# Active connections
ps aux | grep gunicorn

# Celery tasks
celery -A rubber_farm_api inspect active

# Redis info
redis-cli info
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u SERVICE_NAME -n 50

# Check config
sudo systemctl status SERVICE_NAME

# Test manually
source /home/ubuntu/rubberedge/backend/venv/bin/activate
gunicorn rubber_farm_api.wsgi:application  # Test Gunicorn
```

### Database Connection Failed

```bash
# Test connection
psql -h YOUR-RDS-ENDPOINT -U postgres -d rubber_db

# Check environment variables
cat .env | grep DB_

# Verify RDS security group allows EC2
```

### Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### WebSocket Not Working

```bash
# Check Daphne
sudo systemctl status daphne

# View Daphne logs
sudo journalctl -u daphne -f

# Test WebSocket
wscat -c ws://YOUR-IP/ws/chat/1/
```

## 💰 Cost Management

Monitor your AWS usage to stay within free tier:

1. **Set up billing alerts** in AWS Console
2. **Check usage daily** during first week
3. **Review monthly** costs
4. **Clean up** unused resources

See [AWS_FREE_TIER_GUIDE.md](./AWS_FREE_TIER_GUIDE.md) for details.

## 📚 Documentation

- [Main Deployment Guide](./AWS_DEPLOYMENT.md)
- [Free Tier Guide](./AWS_FREE_TIER_GUIDE.md)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Systemd Documentation](https://systemd.io/)

## 🆘 Support

If you encounter issues:

1. Check logs first
2. Review troubleshooting section
3. Search Django/AWS documentation
4. Check Stack Overflow
5. AWS Support (for AWS-specific issues)

## 📝 Notes

- Free tier expires after 12 months
- Monitor billing regularly
- Keep backups of database
- Update dependencies regularly
- Never commit `.env` to git
- Use strong passwords
- Keep Django SECRET_KEY secret

## ✅ Post-Deployment Checklist

- [ ] All services running
- [ ] Database connected
- [ ] Static files loading
- [ ] Media uploads working (S3)
- [ ] WebSocket connections working
- [ ] Celery tasks running
- [ ] SSL certificate installed
- [ ] Billing alerts configured
- [ ] Backups scheduled
- [ ] Mobile app connected
- [ ] Admin panel accessible
- [ ] API endpoints tested

---

For detailed instructions, see [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md).
