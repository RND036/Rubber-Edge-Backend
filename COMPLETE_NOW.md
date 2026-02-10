# 🚀 COMPLETE YOUR DEPLOYMENT IN 60 SECONDS

## ⚠️ Network Issue Detected
Your computer's network is blocking SSH connections (university/corporate firewall).
**Solution:** Use AWS Console's browser-based terminal (bypasses firewall).

---

## 🎯 STEP-BY-STEP (60 seconds)

### Step 1: Open AWS Console (10 seconds)
**Click this link:** https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#ConnectToInstance:instanceId=i-0f916b881089a752f

### Step 2: Connect (10 seconds)
1. You'll see "Connect to instance" page
2. Click the **"EC2 Instance Connect"** tab
3. Keep "ubuntu" as username
4. Click orange **"Connect"** button

A black terminal window will open in your browser.

### Step 3: Copy & Paste This (20 seconds)
**Copy ALL these lines** and paste into the terminal:

```bash
cd ~/rubberedge/backend/api/rubber_chatbot
sed -i 's/from langchain\.tools import tool/from langchain_core.tools import tool/' agents.py
sed -i 's/from langchain\.prompts import ChatPromptTemplate, MessagesPlaceholder/from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder/' agents.py
echo "✅ Imports fixed!"
sudo systemctl restart gunicorn daphne celery celerybeat
echo "⏳ Waiting for services to start..."
sleep 6
echo ""
echo "🧪 Testing deployment..."
curl http://localhost/health/
echo ""
echo ""
echo "✅ If you see {\"status\":\"healthy\"}, deployment is COMPLETE!"
echo "🌐 Your API: http://13.239.135.231/health/"
```

**Press Enter** to execute.

### Step 4: Verify (20 seconds)
You should see:
```json
{"status":"healthy","service":"rubberedge-backend"}
```

**That's it! Deployment complete!** 🎉

---

## 🌐 Test From Your Browser

Open these URLs to verify everything works:

1. **Health Check:** http://13.239.135.231/health/
2. **API Root:** http://13.239.135.231/api/
3. **Admin Panel:** http://13.239.135.231/admin/

---

## 📱 Update Your Mobile App

Change your BASE_URL to:
```javascript
const BASE_URL = "http://13.239.135.231/api";
```

---

## 🔐 Create Admin User (Optional)

In the same EC2 Instance Connect terminal:
```bash
cd ~/rubberedge/backend
source venv/bin/activate
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

---

## 📊 Your Deployment Summary

✅ **EC2 Instance:** i-0f916b881089a752f (RUNNING)  
✅ **Public IP:** 13.239.135.231  
✅ **Region:** ap-southeast-2 (Sydney)  
✅ **Database:** PostgreSQL RDS (42 migrations applied)  
✅ **Services:** Gunicorn, Daphne, Celery, Nginx (all configured)  
✅ **Dependencies:** 100+ packages installed  
✅ **Files:** All deployed  

**Only needs:** 2 import lines fixed (what you're doing above!)

---

## 💡 Why This Works

- **SSH from your computer:** ❌ Blocked by firewall
- **EC2 Instance Connect:** ✅ Uses HTTPS (port 443) - always works
- **Takes:** 60 seconds total

---

## 🆘 If You See An Error

### Error: "502 Bad Gateway" after fix
```bash
# Check logs
sudo tail -20 /var/log/gunicorn/error.log

# Restart again
sudo systemctl restart gunicorn daphne celery celerybeat
sleep 5
curl http://localhost/health/
```

### Error: "Connection refused"
```bash
# Check if services are running
systemctl status gunicorn
systemctl status nginx

# If not running, start them
sudo systemctl start gunicorn nginx
```

### Need to re-edit agents.py
```bash
cd ~/rubberedge/backend/api/rubber_chatbot
nano agents.py
# Edit lines 10 and 11, save with Ctrl+O, exit with Ctrl+X
```

---

## 🎊 Once Complete

Your API endpoints:
- Health: http://13.239.135.231/health/
- Users: http://13.239.135.231/api/users/
- Buyer Prices: http://13.239.135.231/api/buyer-prices/
- Events: http://13.239.135.231/api/events/
- Carousel: http://13.239.135.231/api/carousel/
- Chat: http://13.239.135.231/api/chat/
- Disease Detection: http://13.239.135.231/api/disease-detection/

WebSocket:
- ws://13.239.135.231/ws/chat/

---

## 💰 Remember

Your AWS Free Tier includes:
- 750 hours/month EC2 (stop when not using!)
- 750 hours/month RDS
- 5GB S3 storage

**Stop EC2 when done testing:**
```bash
aws ec2 stop-instances --instance-ids i-0f916b881089a752f --region ap-southeast-2
```

**Start it again when needed:**
```bash
aws ec2 start-instances --instance-ids i-0f916b881089a752f --region ap-southeast-2
```

---

**Ready? Click the link above and complete your deployment! 🚀**

https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#ConnectToInstance:instanceId=i-0f916b881089a752f
