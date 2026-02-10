# Free Deployment Guide for Students

## Option 1: Railway.app (Recommended - $5/month FREE)

### Setup:
1. Go to https://railway.app
2. Sign up with your GitHub account (use student email)
3. Click "New Project" → "Deploy from GitHub repo"
4. Connect your repository
5. Railway will auto-detect Django

### Add Services:
- Click "+ New" → "Database" → "PostgreSQL"
- Click "+ New" → "Database" → "Redis"

### Environment Variables (in Railway dashboard):
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*.railway.app
DATABASE_URL=(auto-set by Railway)
REDIS_URL=(auto-set by Railway)
```

### Deploy:
- Push to GitHub → Railway auto-deploys!
- Your URL: `https://your-app.railway.app`

**Cost**: FREE $5/month credit (enough for small apps)

---

## Option 2: Render.com (100% Free but sleeps)

### Setup:
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your repo
5. Configure:
   - **Name**: rubberedge-backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -e . && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `daphne -b 0.0.0.0 -p $PORT rubber_farm_api.asgi:application`

### Add Database & Redis:
- Click "New +" → "PostgreSQL" (FREE)
- Click "New +" → "Redis" (FREE)

### Environment Variables:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*.onrender.com
DATABASE_URL=(copy from Render PostgreSQL)
REDIS_URL=(copy from Render Redis)
```

**Cost**: FREE (sleeps after 15 min inactivity)

---

## Option 3: GitHub Student Developer Pack (Best Long-term)

### Apply:
1. Go to https://education.github.com/pack
2. Verify with your student email/ID
3. Wait 1-7 days for approval

### What You Get:
- **DigitalOcean**: $200 credit (2+ years of hosting)
- **Heroku**: Credits for paid plans
- **Azure**: $100 credit
- **MongoDB Atlas**: Free cluster
- **Many more services**

### After Approval:
Use DigitalOcean App Platform or Heroku for better performance

---

## Quick Start (Railway):

```bash
# 1. Sign up at railway.app
# 2. Install Railway CLI (optional)
npm install -g @railway/cli

# 3. Login
railway login

# 4. Deploy
railway up

# 5. Add PostgreSQL
railway add plugin:postgresql

# 6. Add Redis
railway add plugin:redis

# 7. Set env vars
railway variables set SECRET_KEY="your-secret-key"
railway variables set DEBUG="False"

# 8. Deploy!
git push
```

---

## Environment Variables Needed:

```env
SECRET_KEY=generate-a-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.railway.app,your-domain.onrender.com
DATABASE_URL=postgres://...
REDIS_URL=redis://...
GROQ_API_KEY=your-groq-key-if-needed
TWILIO_ACCOUNT_SID=your-twilio-sid-if-needed
TWILIO_AUTH_TOKEN=your-twilio-token-if-needed
```

---

## Performance Comparison:

| Platform | Cost | Performance | Sleep? | Setup |
|----------|------|-------------|--------|-------|
| Railway | $5/mo credit | ⭐⭐⭐⭐⭐ | No | Easy |
| Render | Free | ⭐⭐⭐ | Yes (15min) | Easy |
| Fly.io | Free | ⭐⭐⭐⭐ | No | Medium |
| PythonAnywhere | Free | ⭐⭐ | No | Easy |

---

## Mobile App Configuration:

After deployment, update your mobile app's API URL:

```javascript
// React Native example
const API_URL = "https://your-app.railway.app";
// or
const API_URL = "https://your-app.onrender.com";
```

---

## Tips:

1. **Apply for GitHub Student Pack today** (takes days to process)
2. **Start with Railway** while waiting
3. **Monitor usage** in Railway dashboard
4. For Render free tier: First API call takes 30s to wake up
5. Keep your repo updated - most platforms auto-deploy from GitHub

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- GitHub Student Pack: https://education.github.com/pack
