# Deployment Status and Next Steps

## Current Situation

### ✅ What's Working
- EC2 instance created: i-0f916b881089a752f
- All files deployed to EC2
- Python environment and dependencies installed
- Database (PostgreSQL RDS) created and migrations applied
- All services configured (Gunicorn, Daphne, Celery, Nginx)
- Local agents.py file has correct langchain imports

### ❌ Current Issue
**Network connectivity problem** - Cannot connect to EC2 instance at 13.239.135.231

All SSH and HTTP connections are timing out, which suggests:
1. **EC2 instance might be stopped** (most likely)
2. Security group rules may have changed
3. Your IP address changed and isn't in the security group
4. EC2 IP address changed
5. Network/firewall blocking connections

## Immediate Actions Required

### Option 1: Check EC2 Status (Recommended)

1. **Open AWS Console:**
   https://ap-southeast-2.console.aws.amazon.com/ec2/

2. **Check instance i-0f916b881089a752f:**
   - Is it showing "running" or "stopped"?
   - What's the current public IP?

3. **If stopped:**
   ```bash
   aws ec2 start-instances \
     --instance-ids i-0f916b881089a752f \
     --region ap-southeast-2
   ```
   
   OR click "Start instance" in the console.

4 **Wait 2-3 minutes** for it to start, then try connecting again.

###  Option 2: Check Security Group

1. **Go to Security Groups in AWS Console:**
   https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#SecurityGroups:

2. **Find the security group attached to your EC2 instance**

3. **Check Inbound Rules:**
   - SSH (port 22): Should allow your IP
   - HTTP (port 80): Should allow 0.0.0.0/0

4. **Find your current IP:**
   ```bash
   curl ifconfig.me
   ```

5. **Update security group if needed** to allow your IP

### Option 3: Use AWS Systems Manager (No SSH needed)

If EC2 is running but SSH is blocked:

1. Go to AWS Systems Manager → Session Manager
2. Click "Start session"
3. Select instance i-0f916b881089a752f
4. Click "Start session" - Opens browser-based terminal

Then run these commands in the SSM session:
```bash
cd ~/rubberedge/backend/api/rubber_chatbot
sed -i 's/from langchain\.tools import tool/from langchain_core.tools import tool/' agents.py
sed -i 's/from langchain\.prompts import/from langchain_core.prompts import/' agents.py
sudo systemctl restart gunicorn daphne celery celerybeat
sleep 3
curl http://localhost/health/
```

### Option 4: EC2 Instance Connect (Browser-based SSH)

1. Go to EC2 Console
2. Select instance i-0f916b881089a752f
3. Click "Connect" button
4. Choose "EC2 Instance Connect"
5. Click "Connect" - Opens terminal in browser

Then run the same commands as Option 3.

## Once Connected - Complete the Deployment

### Step 1: Fix the Imports
```bash
cd ~/rubberedge/backend/api/rubber_chatbot

# Method A: Using sed (quick)
sed -i 's/from langchain\.tools import tool/from langchain_core.tools import tool/' agents.py
sed -i 's/from langchain\.prompts import/from langchain_core.prompts import/' agents.py

# Method B: Manual edit (if sed fails)
nano agents.py
# Change line 10: from langchain.tools → from langchain_core.tools  
# Change line 11: from langchain.prompts → from langchain_core.prompts
# Save with Ctrl+O, Exit with Ctrl+X

# Verify the fix
head -15 agents.py | grep langchain
```

### Step 2: Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart daphne  
sudo systemctl restart celery
sudo systemctl restart celerybeat

# Wait for services to start
sleep 5

# Check status
systemctl is-active gunicorn daphne celery celerybeat
```

### Step 3: Verify Deployment
```bash
# Test locally on EC2
curl http://localhost/health/

# Should return:
# {"status": "healthy", "service": "rubberedge-backend"}

# Check for errors
sudo tail -20 /var/log/gunicorn/error.log
```

### Step 4: Test from Your Computer
```bash
# Once EC2 is accessible again
curl http://13.239.135.231/health/
```

## After Deployment is Complete

### 1. Create Admin User
```bash
ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231
cd ~/rubberedge/backend
source venv/bin/activate
python manage.py createsuperuser
```

### 2. Test All Endpoints

```bash
# Health check
curl http://13.239.135.231/health/

# API root
curl http://13.239.135.231/api/

# Buyer prices  
curl http://13.239.135.231/api/buyer-prices/

# Admin panel (browser)
open http://13.239.135.231/admin/
```

### 3. Update Mobile App

Change BASE_URL in your mobile app to:
```
http://13.239.135.231/api/
```

### 4. Monitor Services

```bash
ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231
cd ~/rubberedge/backend/deployment
./monitor.sh
```

## Scripts Available

All these scripts are ready in your backend folder:

| Script | Purpose |
|--------|---------|
| `complete_deployment.sh` | Upload fixed file and restart services |
| `final_fix.sh` | SSH and fix imports inline |
| `diagnose_connection.sh` | Check SSH/network connectivity |
| `MANUAL_FIX.md` | Complete manual instructions |
| `DEPLOYMENT_COMPLETE.md` | Full deployment documentation |

## AWS CLI Commands

```bash
# Check instance status
aws ec2 describe-instances \
  --instance-ids i-0f916b881089a752f \
  --region ap-southeast-2 \
  --query 'Reservations[0].Instances[0].State.Name'

# Get current IP
aws ec2 describe-instances \
  --instance-ids i-0f916b881089a752f \
  --region ap-southeast-2 \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# Start instance
aws ec2 start-instances \
  --instance-ids i-0f916b881089a752f \
  --region ap-southeast-2

# Stop instance (to save costs when not using)
aws ec2 stop-instances \
  --instance-ids i-0f916b881089a752f \
  --region ap-southeast-2
```

## Troubleshooting

### Error: "Connection timed out"
- Instance is stopped → Start it
- Security group blocks your IP → Add your IP
- Try from different network

### Error: "502 Bad Gateway"
- Gunicorn workers failing → Check logs
- Import errors not fixed → Complete Step 1
- Socket path wrong → Check nginx config

### Error: "ModuleNotFoundError: langchain.prompts"
- Imports not fixed yet → Complete Step 1
- Wrong Python environment → Use venv

## Cost Reminder

Your AWS resources are running on Free Tier:
- **EC2 t2.micro**: 750 hours/month free (stop when not using)
- **RDS db.t3.micro**: 750 hours/month free
- **S3**: 5GB free

**Remember to stop EC2 when not using to stay within free tier!**

```bash
# Stop EC2 to save hours
aws ec2 stop-instances --instance-ids i-0f916b881089a752f --region ap-southeast-2
```

## Summary

**You're 99% done!** Just need to:
1. ✅ Check why EC2 is unreachable (probably stopped)
2. ✅ Start the instance if needed
3. ✅ Connect via any method (SSH, SSM, Instance Connect)
4. ✅ Fix 2 import lines (30 seconds)
5. ✅ Restart services (30 seconds)
6. ✅ Test health endpoint

Total time: **5 minutes once you can connect to EC2**

Everything else is already set up and working!

---

**Quick Links:**
- EC2 Console: https://ap-southeast-2.console.aws.amazon.com/ec2/
- Instance Details: https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#InstanceDetails:instanceId=i-0f916b881089a752f
- Systems Manager: https://ap-southeast-2.console.aws.amazon.com/systems-manager/session-manager
- Security Groups: https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#SecurityGroups:
