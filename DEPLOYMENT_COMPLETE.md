# Complete Deployment - Final Steps

Your application is **99% deployed** on AWS! Just need to fix one import issue.

## Current Status
✅ EC2 Instance running (13.239.135.231)
✅ RDS PostgreSQL database created and migrated  
✅ S3 bucket configured for med ia storage
✅ All services installed (Gunicorn, Daphne, Celery, Nginx)
✅ Redis running
⚠️ Gunicorn workers failing due to langchain import error

## Fix in 2 Minutes

Open a NEW terminal and run these commands:

```bash
# 1. Fix the imports on EC2
ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231

# Once connected to EC2, run:
cd rubberedge/backend/api/rubber_chatbot
sed -i 's/langchain\.tools/langchain_core.tools/' agents.py
sed -i 's/langchain\.prompts/langchain_core.prompts/' agents.py

# 2. Restart all services
sudo systemctl restart gunicorn daphne celery celerybeat

# 3. Wait a moment and test
sleep 5
curl http://localhost/health/
```

You should see:
```json
{"status": "healthy", "service": "rubberedge-backend"}
```

## Your Live URLs

Once fixed, access your application at:

- **API Base**: http://13.239.135.231/api/
- **Admin Panel**: http://13.239.135.231/admin/  
- **Health Check**: http://13.239.135.231/health/
- **API Docs**: http://13.239.135.231/api/ (if configured)

## Test Your API

```bash
# Test from your Mac:
curl http://13.239.135.231/health/
curl http://13.239.135.231/api/
```

## Service Management Commands

```bash
# Check status
sudo systemctl status gunicorn
sudo systemctl status daphne
sudo systemctl status celery
sudo systemctl status nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/gunicorn/error.log

# Restart if needed
sudo systemctl restart gunicorn daphne celery celerybeat
```

## What Was Deployed

### Infrastructure:
- **EC2**: t2.micro (1 vCPU, 1GB RAM)
- **RDS**: PostgreSQL db.t3.micro  
- **S3**: rubberedge-media-1770656563
- **Region**: ap-southeast-2 (Sydney)

### Services Running:
- **Gunicorn**: WSGI server (port 8000)
- **Daphne**: ASGI/WebSocket server (port 8001)  
- **Celery**: Background task worker
- **Celery Beat**: Scheduled tasks
- **Nginx**: Reverse proxy (port 80)
- **Redis**: Caching & channels

### Database:
- All migrations applied ✅
- Database: `rubber_db`
- Host: `rubberedge-db.cj8okskwm2fz.ap-southeast-2.rds.amazonaws.com`

## Next Steps for Mobile App

Update your mobile app to point to:
```
BASE_URL=http://13.239.135.231/api/
```

##  Costs (Free Tier)
- EC2 t2.micro: Free for 12 months (750 hours/month)
- RDS db.t3.micro: Free for 12 months (750 hours/month)
- S3: Free (5GB storage, 20K GET, 2K PUT per month)

**Estimated**: $0/month for first year if staying within limits!

## Troubleshooting

If health check still fails after fixing imports:

 ```bash
# Check what's preventing startup
sudo journalctl -u gunicorn -n 50 --no-pager

# Test manually
cd ~/rubberedge/backend
source venv/bin/activate
python manage.py check
```

## Support Files Created

All deployment files are in `backend/deployment/`:
- System service files (systemd/)
- Nginx configuration (nginx/)
- Monitor scripts
- Backup scripts
- Deployment guides

---

**You're almost there! Just run those 3 commands on EC2 and your app will be live! 🚀**
