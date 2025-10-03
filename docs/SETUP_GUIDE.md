# 🚀 OpenLearn Colombia - Complete Setup Guide

## **Prerequisites**

Before you begin, ensure you have:
- **Python 3.9+** installed
- **PostgreSQL 14+** installed and running
- **Redis 6+** installed and running
- **Node.js 18+** installed
- **Git** installed

---

## **Option 1: Docker Setup (Recommended - Easiest)**

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/bjpl/open_learn_co.git
cd open_learn_co
```

### **Step 2: Start All Services with Docker**
```bash
# Start core services (PostgreSQL, Redis, API, Frontend)
docker-compose up -d

# Wait 30 seconds for services to initialize
# Check logs to ensure everything started
docker-compose logs -f api
```

### **Step 3: Access the Application**
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### **Optional Development Tools**
```bash
# Start with development tools (PGAdmin, Redis Commander)
docker-compose --profile development up -d

# Access tools:
# - PGAdmin: http://localhost:5050 (admin@colombian-platform.com / admin)
# - Redis Commander: http://localhost:8081
```

### **Optional Monitoring Stack**
```bash
# Start with monitoring (Prometheus, Grafana)
docker-compose --profile monitoring up -d

# Access monitoring:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3001 (admin / admin)
```

---

## **Option 2: Manual Setup (More Control)**

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/bjpl/open_learn_co.git
cd open_learn_co
```

### **Step 2: Setup PostgreSQL Database**

**Install PostgreSQL** (if not installed):
```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt install postgresql-14
sudo systemctl start postgresql

# Windows
# Download installer from: https://www.postgresql.org/download/windows/
```

**Create Database and User**:
```bash
# Connect to PostgreSQL
psql postgres

# In psql prompt:
CREATE DATABASE openlearn;
CREATE USER openlearn WITH PASSWORD 'openlearn123';
GRANT ALL PRIVILEGES ON DATABASE openlearn TO openlearn;
\q
```

### **Step 3: Setup Redis**

**Install Redis** (if not installed):
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Windows
# Download from: https://redis.io/download or use WSL
```

**Verify Redis is running**:
```bash
redis-cli ping
# Should return: PONG
```

### **Step 4: Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download Spanish NLP model
python -m spacy download es_core_news_sm
```

### **Step 5: Configure Environment Variables**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**CRITICAL: Update these values in `.env`:**
```bash
# Database (match what you created in Step 2)
DATABASE_URL=postgresql://openlearn:openlearn123@localhost:5432/openlearn

# Redis
REDIS_URL=redis://localhost:6379/0

# Security - GENERATE A NEW SECRET KEY!
# Run this to generate:
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Then paste the output:
SECRET_KEY=<paste-generated-key-here>

# CORS - Add your frontend URL
CORS_ORIGINS=http://localhost:3000

# Environment
ENVIRONMENT=development
DEBUG=true
```

### **Step 6: Initialize Database**

```bash
# Still in backend directory with venv activated

# Run database migrations
alembic upgrade head

# Verify database connection
python -c "from app.database.connection import check_db_connection; print('DB OK' if check_db_connection() else 'DB FAILED')"
```

### **Step 7: Start Backend Server**

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server should start and show:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify backend is running**:
- Open http://localhost:8000/docs in your browser
- You should see the API documentation (Swagger UI)

### **Step 8: Frontend Setup (New Terminal)**

```bash
# Open a NEW terminal window
cd open_learn_co/frontend

# Install dependencies
npm install

# Start development server
npm start

# Frontend should start on http://localhost:3000
```

### **Step 9: Verify Everything Works**

1. **Frontend**: Open http://localhost:3000 - You should see the dashboard
2. **Backend API**: Open http://localhost:8000/docs - You should see Swagger docs
3. **Health Check**: Visit http://localhost:8000/api/v1/health

Expected health check response:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

---

## **Testing the Platform**

### **Test 1: Database Connection**
```bash
cd backend
source venv/bin/activate
python -c "from app.database.connection import check_db_connection; print(check_db_connection())"
# Should print: True
```

### **Test 2: Check Pool Status**
```bash
python -c "from app.database.connection import get_pool_status; import json; print(json.dumps(get_pool_status(), indent=2))"
# Should show connection pool stats
```

### **Test 3: API Request**
```bash
curl http://localhost:8000/api/v1/health
# Should return JSON with status: healthy
```

---

## **Common Issues & Solutions**

### **Issue 1: Database Connection Failed**
```bash
# Check if PostgreSQL is running
psql postgres -c "SELECT version();"

# If not running:
# macOS: brew services start postgresql@14
# Linux: sudo systemctl start postgresql
# Windows: Start from Services panel
```

### **Issue 2: Redis Connection Failed**
```bash
# Check if Redis is running
redis-cli ping

# If not running:
# macOS: brew services start redis
# Linux: sudo systemctl start redis
# Windows: Start from WSL or install Redis for Windows
```

### **Issue 3: Port Already in Use**
```bash
# Backend port 8000 in use:
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000  # Windows (then kill process)

# Frontend port 3000 in use:
lsof -ti:3000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :3000  # Windows (then kill process)
```

### **Issue 4: Module Not Found Errors**
```bash
# Reinstall backend dependencies
cd backend
pip install --upgrade -r requirements.txt

# Reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### **Issue 5: SpaCy Model Not Found**
```bash
# Download Spanish model
python -m spacy download es_core_news_sm

# Verify installation
python -c "import spacy; nlp = spacy.load('es_core_news_sm'); print('Model loaded successfully')"
```

---

## **Next Steps**

### **1. Run Your First Scraper**
```bash
cd backend
source venv/bin/activate

# Test El Tiempo scraper
python -c "
from scrapers.sources.media.el_tiempo import ElTiempoScraper
scraper = ElTiempoScraper()
print('Scraper initialized successfully')
"
```

### **2. Explore the API**
Visit http://localhost:8000/docs and try these endpoints:
- `GET /api/v1/health` - Health check
- `GET /api/v1/sources` - List data sources
- `GET /api/v1/articles` - Retrieve articles

### **3. Add API Keys (Optional)**
Edit `.env` and add your API keys:
```bash
DANE_API_KEY=your_key_here
SECOP_API_TOKEN=your_token_here
IDEAM_API_KEY=your_key_here
```

### **4. Configure Scrapers**
- Default scraping runs every 30 minutes
- Adjust in `.env`: `SCRAPING_INTERVAL_MINUTES=30`
- Disable: `ENABLE_SCHEDULER=False`

---

## **Production Deployment**

When ready for production:

1. **Generate secure SECRET_KEY**:
```bash
python backend/scripts/generate_secret_key.py
```

2. **Update `.env` for production**:
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<your-64-byte-secure-key>
DATABASE_URL=<production-database-url>
CORS_ORIGINS=https://yourdomain.com
```

3. **Use production database** with strong passwords
4. **Enable SSL/TLS** for HTTPS
5. **Set up monitoring** (Sentry, Prometheus, Grafana)

---

## **Quick Reference Commands**

### **Start Everything (Docker)**
```bash
docker-compose up -d
```

### **Start Everything (Manual)**
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm start
```

### **Stop Everything**
```bash
# Docker
docker-compose down

# Manual: Ctrl+C in each terminal
```

### **View Logs**
```bash
# Docker
docker-compose logs -f api

# Manual: Check backend/logs/ directory
```

---

You're now ready to use OpenLearn Colombia! 🇨🇴
