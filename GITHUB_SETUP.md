# Rubber Farm API - GitHub Setup & Deployment Guide

This Django REST API backend supports both mobile and web applications with real-time features, AI disease detection, and price tracking.

## 🚀 Quick Start

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/rubber-farm-backend.git
cd rubber-farm-backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your local configuration
```

5. **Run migrations:**
```bash
python manage.py migrate
```

6. **Create superuser:**
```bash
python manage.py createsuperuser
```

7. **Run development server:**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

---

## 📱 Mobile App Integration

Your Django backend provides REST API endpoints for mobile apps (iOS/Android).

### API Base URL
- **Development:** `http://localhost:8000`
- **Production:** `https://your-domain.com`

### Authentication
Mobile apps authenticate using JWT tokens obtained from the login endpoint:

```
POST /api/v1/auth/login/
Body: {"username": "user", "password": "pass"}
Response: {"access": "token", "refresh": "token"}
```

Use the `access` token in all subsequent requests:
```
Authorization: Bearer <access_token>
```

### Key Endpoints (Examples)
- **Authentication:** `/api/auth/`, `/api/token/`, `/api/token/refresh/`
- **Users:** `/api/users/`, `/api/users/profile/`
- **Disease Detection:** `/api/diseases/detect/` (POST with image)
- **Chat:** `/api/chat/messages/`, WebSocket at `wss://your-domain.com/ws/chat/`
- **Events:** `/api/events/`
- **Prices:** `/api/buyerprices/`

See `rubber_farm_api/urls.py` for all available endpoints.

---

## 🌐 Deployment Options

### Option 1: Railway (Recommended - Simplest)

1. **Push to GitHub**
2. **Go to [Railway.app](https://railway.app)**
3. **Connect your GitHub repository**
4. **Add PostgreSQL plugin**
5. **Configure environment variables** (Settings → Variables)
6. **Deploy** (Auto-deploys on git push)

**Environment variables to set on Railway:**
```
DEBUG=False
SECRET_KEY=<generate-new>
ALLOWED_HOSTS=<your-railway-domain>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=<railway-postgres-password>
DB_HOST=<railway-postgres-host>
DB_PORT=5432
REDIS_URL=<if using redis>
USE_S3=False (or True if using S3)
```

### Option 2: Render

1. **Push to GitHub**
2. **Go to [Render.com](https://render.com)**
3. **Create new Web Service**
4. **Connect GitHub repository**
5. **Use `render.yaml` configuration** (already in repo)
6. **Configure PostgreSQL**
7. **Deploy**

### Option 3: AWS (Advanced)

Complete AWS deployment scripts are included in the `deployment/` directory:
- `deployment/setup_aws.sh` - Initial setup
- `deployment/deploy.sh` - Deployment script
- `AWS_DEPLOYMENT.md` - Detailed AWS guide

For AWS S3 static file storage, set in environment:
```
USE_S3=True
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_STORAGE_BUCKET_NAME=<bucket-name>
AWS_S3_REGION_NAME=us-east-1
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Generate new `SECRET_KEY`: 
  ```bash
  python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- [ ] Set `DEBUG=False`
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Configure `CORS_ALLOWED_ORIGINS` for your mobile app domain
- [ ] Use environment variables for all sensitive data
- [ ] Use HTTPS/WSS in production
- [ ] Store AWS credentials securely (never commit them)
- [ ] Set strong database password
- [ ] Review `SIMPLE_JWT` token expiration settings

---

## 📋 Environment Variables

Copy `.env.example` to `.env` and configure:

```dotenv
# Django
DEBUG=False
SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL recommended)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rubber_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis (for caching & Celery)
REDIS_URL=redis://localhost:6379/0

# AWS S3 (Optional - for file storage)
USE_S3=False
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=your_bucket
AWS_S3_REGION_NAME=us-east-1

# Twilio SMS (Optional - for OTP/notifications)
TWILIO_ENABLED=False
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# Scraping Tasks
ENABLE_AUTO_SCRAPING=True
```

---

## 🗄️ Database Setup

### PostgreSQL (Recommended for Production)

```bash
# Create database
createdb rubber_db
createuser postgres_user

# Connect Django
# Update environment variables with your PostgreSQL credentials
python manage.py migrate
```

### SQLite (Development Only)
SQLite is used by default for development, but switch to PostgreSQL for production.

---

## 🔧 Key Features

- **REST API** - DRF with JWT authentication
- **Real-time Chat** - WebSocket via Django Channels
- **Disease Detection** - AI/ML model for plant disease identification
- **Price Tracking** - Web scraper for market prices
- **Event Management** - Create and manage farm events
- **Carousel** - Media management system
- **Custom User Model** - Extended user with farmer-specific fields
- **CORS Enabled** - Ready for mobile/web frontend integration
- **Celery Tasks** - Background job processing with Celery Beat scheduler

---

## 📚 Project Structure

```
.
├── api/                    # Main API app (disease detection, scraping)
├── users/                  # User management & authentication
├── chat/                   # WebSocket-based messaging
├── events/                 # Event management
├── carousel/               # Media/carousel management
├── buyerprices/            # Buyer price tracking
├── latex_quality/          # LaTeX quality assessment
├── rubber_farm_api/        # Django project settings
├── deployment/             # AWS deployment scripts & guides
├── requirements.txt        # Python dependencies
├── manage.py              # Django management
├── .env.example           # Environment variables template
└── README.md              # Project documentation
```

---

## 🆘 Troubleshooting

### "ModuleNotFoundError" after deploying
- Run migrations on the server: `python manage.py migrate`
- Install requirements: `pip install -r requirements.txt`

### CORS errors on mobile app
- Update `ALLOWED_HOSTS` with your mobile app's domain
- Configure `CORS_ALLOWED_ORIGINS` if needed
- Check `rubber_farm_api/settings.py` CORS settings

### Database connection errors
- Verify database credentials in `.env`
- Check if database is running
- Ensure database user has correct permissions

### WebSocket connection issues
- Use WSS (secure WebSocket) in production
- Ensure `ASGI_APPLICATION` is correctly configured
- Check that Daphne server is running

---

## 📖 Documentation

- **API Docs:** Access at `/admin/` (Django admin)
- **Settings:** See `rubber_farm_api/settings.py`
- **AWS Guide:** See `AWS_DEPLOYMENT.md`
- **Deployment:** See `deployment/DEPLOYMENT_CHECKLIST.md`

---

## 📞 Support

For issues or questions:
1. Check existing documentation files
2. Review Django/DRF official docs
3. Check Channels documentation for WebSocket issues

---

## 📄 License

[Add your license here]

---

**Ready to deploy!** Push to GitHub and select your deployment platform above. 🚀
