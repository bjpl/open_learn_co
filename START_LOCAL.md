# 🚀 OpenLearn Colombia - Quick Start Guide

## Get Running in 5 Minutes

### Step 1: Start Infrastructure (1 minute)
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify they're running
docker-compose ps
```

### Step 2: Initialize Database (1 minute)
```bash
cd backend

# Install dependencies (if not done)
pip install -r requirements.txt

# Run migrations
python -m alembic upgrade head

# Verify database
python -c "from app.database.connection import init_db; import asyncio; asyncio.run(init_db())"
```

### Step 3: Start Backend (1 minute)
```bash
# In terminal 1
cd backend
uvicorn app.main:app --reload --port 8000

# Should see: "Application startup complete"
# Test: http://localhost:8000/docs
```

### Step 4: Start Frontend (1 minute)
```bash
# In terminal 2
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev

# Should see: "Ready on http://localhost:3000"
```

### Step 5: Verify Everything Works (1 minute)

**Test Backend:**
```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

**Test Frontend:**
- Open: http://localhost:3000
- You should see the dashboard

**Test Scraping:**
```bash
curl -X POST http://localhost:8000/api/v1/scraping/scrape \
  -H "Content-Type: application/json" \
  -d '{"source": "el_tiempo", "count": 3}'
```

---

## Daily Usage

### Start System
```bash
# Terminal 1: Infrastructure
docker-compose up -d

# Terminal 2: Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend && npm run dev
```

### Stop System
```bash
# Ctrl+C in backend and frontend terminals

# Stop infrastructure
docker-compose down
```

---

## Troubleshooting

### "Port 5432 already in use"
```bash
# Stop existing PostgreSQL
sudo service postgresql stop  # Linux
brew services stop postgresql  # macOS
```

### "Module not found"
```bash
cd backend
pip install -r requirements.txt
```

### "Database connection failed"
```bash
# Check Docker logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up -d postgres
```

### "Frontend won't start"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## What's Next?

1. **Explore the Dashboard**: http://localhost:3000
2. **Test Scrapers**: Try different Colombian news sources
3. **Check API Docs**: http://localhost:8000/docs
4. **Set Up Scheduling**: Add daily scraping jobs
5. **Deploy to Production**: Follow DEPLOYMENT_WALKTHROUGH.md

---

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main dashboard |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache/Queue |

---

**Need Help?** Check the logs:
```bash
# Backend logs
tail -f backend/logs/app.log

# Docker logs
docker-compose logs -f
```
