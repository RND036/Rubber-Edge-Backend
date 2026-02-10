# RubberEdge Backend - Complete Architecture Guide

## 🏗️ Overall Architecture

Your backend is a **Django REST API** with real-time WebSocket support, built for agricultural (rubber farming) market data and farmer communication. It's structured as a multi-app Django project using an ASGI/WSGI hybrid architecture.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Mobile)                   │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │        HTTP/REST API            │      WebSocket
          ▼                                  ▼
┌──────────────────────────────────────────────────────────────┐
│             Django REST Framework (DRF)                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Authentication (JWT)  │  CORS  │  Serializers  │ Views  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────────────┐
          │                │                        │
          ▼                ▼                        ▼
    ┌──────────┐    ┌──────────────┐         ┌──────────────┐
    │ PostgreSQL│    │  Redis Cache  │         │   AWS S3      │
    │  Database │    │  (Celery)     │         │  (File Storage)│
    └──────────┘    └──────────────┘         └──────────────┘
          │
    ┌─────────────────────────────────────┐
    │   7 Django Apps (Models + Views)     │
    └─────────────────────────────────────┘
```

---

## 🛠️ Key Technologies Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Django 4.2 | Web framework |
| **API** | Django REST Framework | RESTful API endpoints |
| **Real-time** | Django Channels | WebSocket for live chat/events |
| **Authentication** | JWT (Simple JWT) | Token-based auth |
| **Background Jobs** | Celery + Redis | Async task processing |
| **Database** | PostgreSQL | Primary data storage |
| **Cache/Message Broker** | Redis | Celery, Channel Layers |
| **File Storage** | AWS S3 (optional) | Image/media files |
| **Web Server** | Daphne (ASGI) | WebSocket + HTTP |
| **SMS** | Twilio | OTP sending |
| **Web Scraping** | BeautifulSoup | Market price scraping |
| **ML Models** | TensorFlow Lite | Disease detection |

---

## 📊 Database Models & Data Storage

### 1. **Users App** - Authentication & User Management

**Location:** `users/models.py`

**Key Model: User (Custom Auth User)**
```
User
├── phone_number ⭐ (unique identifier - Sri Lanka format)
├── role (farmer, buyer, officer)
├── is_verified (phone OTP verified)
├── failed_otp_attempts
├── created_at, updated_at
└── is_active, is_staff (admin)

Storage: PostgreSQL (users table)
```

**Purpose:** 
- Phone-based authentication (no password needed initially)
- OTP verification via SMS/Twilio
- Role-based access control (RBAC)

---

### 2. **API App** - Market Data & Disease Detection

**Location:** `api/models.py`

#### A. **RubberPrice** - Auction Prices
```
RubberPrice
├── grade (RSS1, RSS2, RSS3, etc.)
├── price (decimal)
├── auction_date (when price was published)
├── change_percentage (vs previous auction)
└── created_at, updated_at

Unique Together: (grade, auction_date)
Indexes: auction_date, grade
Storage: PostgreSQL
Updated By: Celery task (scrape_rrisl_prices_task)
```

#### B. **MarketStats** - Market Overview
```
MarketStats
├── date (unique)
├── week_high, week_low
├── month_high, month_low
├── avg_volume
└── created_at, updated_at

Storage: PostgreSQL
Updated By: Manual scraping endpoint
```

#### C. **ScrapingLog** - Audit Trail
```
ScrapingLog
├── timestamp
├── success (bool)
├── grades_scraped (count)
├── error_message
├── source_url
└── Provides: Debugging info for price scraping

Storage: PostgreSQL
```

#### D. **DiseaseDetectionLog** - ML Model Tracking
```
DiseaseDetectionLog
├── timestamp
├── disease_detected (name)
├── confidence (%)
├── processing_time_ms
├── success (bool)
└── error_message

Storage: PostgreSQL
Used For: Monitoring ML model accuracy
```

---

### 3. **Chat App** - Real-time Chatbot & Conversations

**Location:** `chat/models.py`

#### A. **Conversation** - Direct Messages
```
Conversation (1-to-1)
├── farmer (FK to User)
├── officer (FK to User)
├── created_at
└── Unique: (farmer, officer) pair

Storage: PostgreSQL
Real-time: WebSocket updates via Channels
```

#### B. **Message** - Chat Content
```
Message
├── conversation (FK)
├── sender (FK to User)
├── text (content)
├── is_read (bool)
└── created_at

Storage: PostgreSQL
Real-time Delivery: Via Django Channels WebSocket
```

---

### 4. **Rubber Chatbot** - AI-Powered Queries

**Location:** `api/models.py` (part of API)

#### A. **ChatSession** - Bot Conversation Context
```
ChatSession
├── session_id (unique key)
├── user (FK - optional for anonymous)
├── created_at, updated_at
├── is_active
└── Related: messages, disease_queries, shop_queries

Storage: PostgreSQL
Purpose: Track multi-turn chatbot conversations
```

#### B. **ChatMessage** - Bot Conversation Turns
```
ChatMessage
├── session (FK)
├── message_type (user, bot, system)
├── content (text)
├── metadata (JSON for extra data)
└── timestamp

Storage: PostgreSQL
Order: Chronological
```

#### C. **DiseaseQuery** - Disease Identification
```
DiseaseQuery
├── session (FK)
├── disease_name
├── query_text (user question)
├── bot_response (answer)
├── confidence_score
└── timestamp

Storage: PostgreSQL
Purpose: Track disease queries for analytics
```

#### D. **ShopQuery** - Location-Based Product Lookup
```
ShopQuery
├── session (FK)
├── product_type
├── location
├── query_text
├── bot_response
└── timestamp

Storage: PostgreSQL
Purpose: Help farmers find nearby shops
```

---

### 5. **Events App** - Workshops & Training

**Location:** `events/models.py`

#### A. **Event**
```
Event
├── title
├── description
├── event_date (when event happens)
├── location
├── created_by (FK to User - who created it)
├── image (upload_to='events/%Y/%m/')
├── is_active, is_cancelled
├── max_participants
├── contact_number
└── created_at, updated_at

Storage: 
  - Metadata: PostgreSQL
  - Image: AWS S3 or local /media/events/
Indexes: event_date, created_by, is_active
```

#### B. **EventAttendance**
```
EventAttendance
├── event (FK)
├── farmer (FK to User)
├── status (interested, attending, attended, not_attending)
├── registered_at
└── Unique: (event, farmer)

Storage: PostgreSQL
Purpose: Track who's attending which events
```

---

### 6. **Carousel App** - Dashboard Hero Section

**Location:** `carousel/models.py`

#### CarouselItem
```
CarouselItem
├── title (optional)
├── value (optional)
├── subtitle (optional)
├── image ⭐ (required - upload_to='carousel/%Y/%m/')
├── color (hex code for overlay)
├── icon (ionicon name)
├── order (display sequence)
├── is_active
├── created_at, updated_at

Storage:
  - Metadata: PostgreSQL
  - Image: AWS S3 or local /media/carousel/
Order: By 'order' field, newest first
```

---

### 7. **Buyer Prices App** - Buyer-to-Farmer Pricing

**Location:** `buyerprices/models.py` (not fully shown, but similar structure)

```
Purpose: Track buyer offers to farmers
Likely Contains:
├── Buyer info
├── Offered prices
├── Quality grades
└── Timestamps
```

---

### 8. **LaTeX Quality App** - Document Generation

**Location:** `latex_quality/models.py`

```
Purpose: Likely for generating PDF reports
├── LaTeX templates
├── Document metadata
└── Generated PDFs
```

---

## 📁 File Storage Locations

### Development (Local Files)
```
/backend/
├── /media/
│   ├── /carousel/
│   │   └── 2025/02/image.jpg
│   ├── /events/
│   │   └── 2025/02/image.jpg
│   └── ...
├── /staticfiles/
│   └── CSS, JS, static files
└── dump.rdb (Redis persistence)
```

### Production (AWS S3)
If `USE_S3=true` and AWS credentials are set:

```
S3 Bucket Structure:
├── /static/
│   └── CSS, JS files
├── /media/
│   ├── /carousel/
│   │   └── 2025/02/image.jpg
│   ├── /events/
│   │   └── 2025/02/image.jpg
│   └── /uploads/
└── URLs: https://bucket-name.s3.amazonaws.com/media/...
```

### Database Backups
```
AWS credentials: AWS_CREDENTIALS.txt
Backup scripts: deploy_direct.sh, deploy_to_aws.sh
Redis dump: dump.rdb (in-memory cache)
```

---

## 🔄 Data Flow - How Data Moves Through System

### 1. **User Authentication Flow**
```
User (Phone: +94771234567)
    ↓
POST /api/auth/request-otp/
    ↓
✖️ Check if user exists → Yes: fetch user | No: create new user
    ↓
Send OTP via Twilio (or print to console in dev)
    ↓
User inputs OTP
    ↓
POST /api/auth/verify-otp/
    ↓
Validate OTP + check attempts → Success
    ↓
Generate JWT ACCESS_TOKEN (1 day) + REFRESH_TOKEN (7 days)
    ↓
Return tokens → User authenticated
```

### 2. **Rubber Price Flow (Scraping)**
```
[Scheduled] Tuesday 10:00 AM
    ↓
Celery Beat triggers: scrape_rrisl_prices_task
    ↓
Celery Worker (background process) fetches task
    ↓
BeautifulSoup scrapes: https://www.rrisl.lk/
    ↓
Parse HTML → Extract RSS grades and prices
    ↓
Save to PostgreSQL: RubberPrice table
    ↓
Calculate price change vs previous auction
    ↓
Update MarketStats table
    ↓
Log success in ScrapingLog
    ↓
API endpoint returns latest prices to frontend
```

### 3. **Disease Detection Flow**
```
Farmer captures rubber leaf image
    ↓
POST /api/disease-detection/
    + Image file
    + TensorFlow Lite model: rubber_disease_model.tflite
    ↓
Backend processes image:
  1. Resize & normalize
  2. Run ML model inference
  3. Get disease class + confidence %
    ↓
Save to DiseaseDetectionLog (audit trail)
    ↓
If part of chat session → also save to ChatMessage
    ↓
Return diagnosis to farmer
```

### 4. **Real-time Chat Flow**
```
Farmer sends message
    ↓
WebSocket connection → Channels
    ↓
Message saved to PostgreSQL: ChatMessage
    ↓
Channels broadcasts message to recipient
    ↓
Officer receives in real-time (WebSocket)
    ↓
Officer types response
    ↓
Repeat (same flow)
    ↓
Optional: Save to Conversation table for history
```

### 5. **Event Registration Flow**
```
Officer creates event
    ↓
POST /api/events/
    + Title, description, date, image
    + Image uploaded → AWS S3 or /media/events/
    ↓
Save to PostgreSQL: Event table
    ↓
Event appears on farmer dashboard
    ↓
Farmer clicks "Interested" or "Attending"
    ↓
POST /api/events/{event_id}/register/
    ↓
Save to PostgreSQL: EventAttendance table
    ↓
Officer can see attendance count
    ↓
When event date arrives, mark as "attended"
```

---

## 🔌 API Endpoints Summary

### Authentication
```
POST   /api/auth/request-otp/      → Send OTP to phone
POST   /api/auth/verify-otp/       → Verify OTP, get JWT tokens
POST   /api/auth/refresh/          → Get new access token
```

### Rubber Prices
```
GET    /api/prices/                → Get latest prices
GET    /api/prices/history/        → Get historical data
GET    /admin/                     → Admin scraping controls
```

### Disease Detection
```
POST   /api/disease-detection/     → Upload image, get diagnosis
GET    /api/disease-detection/logs/ → View detection history
```

### Chat
```
WebSocket: /ws/chat/{session_id}/  → Real-time messaging
GET    /api/chat/conversations/    → List conversations
POST   /api/chat/messages/         → Send message
```

### Events
```
GET    /api/events/                → List all events
POST   /api/events/                → Create event (admin)
GET    /api/events/{id}/           → Get event details
POST   /api/events/{id}/register/  → Register attendance
```

### Chatbot
```
POST   /api/chatbot/ask/           → Ask disease question
POST   /api/chatbot/shop-search/   → Find nearby shops
```

---

## ⚙️ Background Tasks (Celery)

**Broker/Cache:** Redis at `redis://localhost:6379/0`

### Scheduled Tasks (Celery Beat)
```
Task: scrape_rrisl_prices_task
├── Schedule: Every Tuesday 10:00 AM
├── Backup: Every Monday 4:00 PM
├── Action: Scrape RRISL website, save prices
└── Storage: PostgreSQL RubberPrice table

Enable/Disable: ENABLE_AUTO_SCRAPING setting
```

### On-Demand Tasks
```
Tasks can be triggered from views:
├── Send email/SMS
├── Generate PDF reports
├── Process large image uploads
├── Clean up old logs
└── Database maintenance
```

---

## 🔐 Authentication & Authorization

### JWT Tokens
```
Payload structure:
{
  "token_type": "access",
  "exp": 1707500000,        # 1 day lifetime
  "user_id": 1,
  "phone_number": "+94771234567",
  "role": "farmer"
}

Refresh Token: Valid for 7 days
Token Location: Authorization: Bearer {token}
```

### Role-Based Access Control (RBAC)
```
Roles:
├── farmer     → Can view prices, do disease detection, join events
├── buyer      → Can view farmer data, post prices
└── officer    → Admin access, manage events, view all data
```

---

## 📊 Database Schema - Key Tables

```sql
-- Authentication & Users
users (id, phone_number, role, is_verified, failed_otp_attempts, ...)

-- Market Data
api_rubberprice (id, grade, price, auction_date, change_percentage, ...)
api_marketstats (id, date, week_high, week_low, month_high, month_low, ...)
api_scrapinglog (id, timestamp, success, grades_scraped, error_message, ...)

-- Disease Detection
api_diseasedetectionlog (id, disease_detected, confidence, processing_time_ms, ...)

-- Chat & Conversations
chat_conversation (id, farmer_id, officer_id, created_at, ...)
chat_message (id, conversation_id, sender_id, text, is_read, created_at, ...)

-- Chatbot Sessions
api_chatsession (id, session_id, user_id, created_at, is_active, ...)
api_chatmessage (id, session_id, message_type, content, metadata, ...)
api_diseasequery (id, session_id, disease_name, query_text, confidence_score, ...)
api_shopquery (id, session_id, product_type, location, query_text, ...)

-- Events
events_event (id, title, description, event_date, created_by_id, image, ...)
events_eventattendance (id, event_id, farmer_id, status, registered_at, ...)

-- UI Components
carousel_carouselitem (id, title, value, subtitle, image, order, is_active, ...)

-- Logs
django_admin_log (for admin changes)
```

---

## 🚀 Environment Configuration

### Key Settings (.env file)
```bash
# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rubber_db
DB_USER=ravishkadissanayaka
DB_HOST=localhost
DB_PORT=5432

# Redis/Celery
REDIS_URL=redis://localhost:6379/0

# AWS S3 (if using cloud storage)
USE_S3=False
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...

# SMS/Twilio
TWILIO_ENABLED=False
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# Auto Scraping
ENABLE_AUTO_SCRAPING=True

# Debug
DEBUG=True
ALLOWED_HOSTS=*
```

---

## 📈 Data Persistence & Backups

```
What's Stored Where:

✅ PostgreSQL (Persistent - survives restart)
  ├── All user data
  ├── Price history
  ├── Chat messages
  ├── Events & attendance
  └── Logs

⚠️ Redis (Volatile - can be lost)
  ├── Celery task queue
  ├── Channel layer (WebSocket routing)
  ├── Cache
  └── Session data

❌ dump.rdb (Local Redis persistence)
  └── Backup of Redis state

📦 AWS S3 or /media/ (File Storage)
  ├── Carousel images
  ├── Event images
  └── User uploads

Backup Strategy:
  - Use deployment scripts: deploy.sh, backup_db.sh
  - Run health checks: health_check.sh
  - Monitor with: monitor.sh
```

---

## 🔍 Data Flow Summary Diagram

```
FRONTEND (React/Mobile)
    │
    ├─→ REST API (/api/...) → Django Views → Business Logic → PostgreSQL
    │
    └─→ WebSocket (/ws/...) → Channels → Real-time Updates → Redis → Browser
    
BACKGROUND PROCESSES:
    Celery Worker ← Redis Broker ← Celery Beat (Scheduler)
        │
        └─→ Scrape RRISL → Save prices → Update frontend

EXTERNAL INTEGRATIONS:
    ├─→ Twilio (SMS/OTP)
    ├─→ AWS S3 (File Storage)
    └─→ RRISL Website (Web Scraping)

MACHINE LEARNING:
    TensorFlow Lite Model → Disease Detection → Save results → Return response
```

---

## 🎯 Quick Data Lookup Guide

**"Where is X data stored?"**

| Data | Location | Table | Updated By |
|------|----------|-------|------------|
| User phone/auth | PostgreSQL | `users` | API endpoints |
| Rubber prices | PostgreSQL | `api_rubberprice` | Celery scraping task |
| Chat messages | PostgreSQL | `chat_message` | WebSocket handler |
| Events | PostgreSQL + S3 | `events_event` | Admin interface |
| Event attendance | PostgreSQL | `events_eventattendance` | API endpoints |
| Disease predictions | PostgreSQL | `api_diseasedetectionlog` | ML API endpoint |
| Carousel images | PostgreSQL + S3 | `carousel_carouselitem` | Admin interface |
| Conversations | PostgreSQL | `chat_conversation` | WebSocket handler |
| Market stats | PostgreSQL | `api_marketstats` | Scraping task |

---

## 💡 Key Takeaways

1. **Database:** PostgreSQL is the main persistent storage for all data
2. **Cache:** Redis for real-time features (WebSocket, Celery)
3. **Files:** AWS S3 (production) or `/media/` folder (development)
4. **Real-time:** WebSocket via Django Channels for live chat
5. **Async:** Celery for background jobs (scraping every Tuesday)
6. **Authentication:** Phone-based OTP with JWT tokens
7. **Architecture:** Multi-app Django with separate concerns (users, API, chat, events)

This is a sophisticated agricultural platform combining real-time communication, market data, AI disease detection, and event management! 🌾
