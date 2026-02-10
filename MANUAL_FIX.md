# Manual Deployment Completion Guide

## Problem
The langchain imports need to be fixed on the EC2 instance and services need to be restarted.

## Quick Fix - Method 1: Automated Script

```bash
cd /Users/ravishkadissanayaka/Documents/uni/3\ year/FYP/rubberedge/backend
chmod +x complete_deployment.sh
./complete_deployment.sh
```

## Manual Fix - Method 2: Step by Step

If the script fails due to SSH timeouts, follow these manual steps:

### Step 1: SSH into EC2
```bash
ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231
```

### Step 2: Fix the imports
```bash
cd ~/rubberedge/backend/api/rubber_chatbot

# Fix line 10 - tools import
sed -i 's/from langchain\.tools import tool/from langchain_core.tools import tool/' agents.py

# Fix line 11 - prompts import  
sed -i 's/from langchain\.prompts import/from langchain_core.prompts import/' agents.py

# Verify the fix
echo "=== Checking imports ==="
head -15 agents.py | grep -E "langchain|from"
```

### Step 3: Restart all services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart daphne
sudo systemctl restart celery
sudo systemctl restart celerybeat

# Wait a moment
sleep 3

# Check status
systemctl is-active gunicorn daphne celery celerybeat
```

### Step 4: Test the deployment
```bash
# From inside EC2
curl http://localhost/health/

# Should return:
# {"status": "healthy", "service": "rubberedge-backend"}
```

### Step 5: Exit and test from your computer
```bash
exit  # Exit from EC2

# Test from your Mac
curl http://13.239.135.231/health/
```

## Method 3: Quick One-Liner

If you can establish SSH connection, run this all-in-one command:

```bash
ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231 'cd ~/rubberedge/backend/api/rubber_chatbot && sed -i "s/from langchain\.tools import tool/from langchain_core.tools import tool/" agents.py && sed -i "s/from langchain\.prompts import/from langchain_core.prompts import/" agents.py && sudo systemctl restart gunicorn daphne celery celerybeat && sleep 3 && curl http://localhost/health/'
```

## Verification

After completing any method, verify:

1. **Health endpoint works:**
   ```bash
   curl http://13.239.135.231/health/
   ```
   Should return: `{"status": "healthy", "service": "rubberedge-backend"}`

2. **All services are active:**
   ```bash
   ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231 \
     'systemctl is-active gunicorn daphne celery celerybeat'
   ```
   Should show 4 lines of "active"

3. **No import errors in logs:**
   ```bash
   ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231 \
     'sudo tail -20 /var/log/gunicorn/error.log'
   ```
   Should not show "ModuleNotFoundError: No module named 'langchain.prompts'"

## Troubleshooting

### If health endpoint returns 502:
- Check Gunicorn logs: `sudo tail -50 /var/log/gunicorn/error.log`
- Check if socket exists: `ls -la ~/rubberedge/backend/gunicorn.sock`
- Restart Nginx: `sudo systemctl restart nginx`

### If imports still fail:
- Verify Python environment: `source ~/rubberedge/backend/venv/bin/activate && pip list | grep langchain`
- Should show both `langchain` and `langchain-core` packages

### If SSH timeouts persist:
- Check EC2 Security Group allows SSH (port 22) from your IP
- Verify instance is running: AWS Console → EC2 → instance i-0f916b881089a752f
- Try from different network or wait a few minutes

## Next Steps After Successful Deployment

1. **Create Admin User:**
   ```bash
   ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231 \
     'cd ~/rubberedge/backend && source venv/bin/activate && python manage.py createsuperuser'
   ```

2. **Update Mobile App:**
   - Change BASE_URL to: `http://13.239.135.231/api/`

3. **Monitor Services:**
   ```bash
   ssh -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231 \
     'cd ~/rubberedge/backend/deployment && ./monitor.sh'
   ```

4. **Set up domain (optional):**
   - Point domain DNS to: 13.239.135.231
   - Update Nginx config with domain name
   - Set up SSL with Let's Encrypt (see DEPLOYMENT_COMPLETE.md)

## API Endpoints to Test

Once deployment is complete:

- Health: `http://13.239.135.231/health/`
- API Root: `http://13.239.135.231/api/`
- Admin Panel: `http://13.239.135.231/admin/`
- Send OTP: `POST http://13.239.135.231/api/users/send-otp/`
- Buyer Prices: `GET http://13.239.135.231/api/buyer-prices/`
- Events: `GET http://13.239.135.231/api/events/`

Your deployment is 99% complete - just need to fix those 2 import lines! 🚀
