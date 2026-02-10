# 🚀 AWS Free Tier Deployment - Quick Start

Your Django backend is now ready to deploy on AWS Free Tier!

## 📍 Start Here

➡️ **[Complete AWS Deployment Guide](deployment/AWS_DEPLOYMENT.md)**

## 📦 What's Included

✅ Complete AWS setup instructions  
✅ Automated deployment scripts  
✅ Systemd service configurations  
✅ Nginx setup with WebSocket support  
✅ Database (RDS) integration  
✅ S3 storage for media files  
✅ Celery for background tasks  
✅ SSL certificate setup  
✅ Monitoring & backup scripts  
✅ Cost optimization guide  

## ⚡ Quick Deploy (3 Steps)

### 1. Launch AWS Resources
- EC2 t2.micro instance (Ubuntu 22.04)
- RDS PostgreSQL db.t2.micro
- S3 bucket for media files

### 2. Run Setup Script on EC2
```bash
ssh -i your-key.pem ubuntu@YOUR-EC2-IP
git clone YOUR-REPO-URL rubberedge
cd rubberedge/backend
./deployment/setup_aws.sh
```

### 3. Configure & Deploy
```bash
# Edit .env with your credentials
nano .env

# Deployment is automatic!
```

## 📚 Documentation

- **[AWS Deployment Guide](deployment/AWS_DEPLOYMENT.md)** - Complete setup instructions
- **[Free Tier Guide](deployment/AWS_FREE_TIER_GUIDE.md)** - Cost limits & optimization
- **[Deployment README](deployment/README.md)** - Scripts & troubleshooting

## 💰 Cost

**Year 1**: FREE (AWS Free Tier)  
**After 12 months**: ~$25-30/month

## 🆘 Need Help?

1. Check [AWS_DEPLOYMENT.md](deployment/AWS_DEPLOYMENT.md)
2. See troubleshooting section
3. Review logs: `./deployment/monitor.sh`

---

**⚠️ Important**: 
- Don't forget to set up billing alerts!
- Keep `.env` file secret (never commit to git)
- Free tier expires after 12 months

**Ready to deploy? Start with [AWS_DEPLOYMENT.md](deployment/AWS_DEPLOYMENT.md)** 🚀
