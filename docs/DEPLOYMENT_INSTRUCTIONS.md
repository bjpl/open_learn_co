# Phase 1 Deployment Instructions
**OpenLearn Colombia - Staging Deployment Guide**
*Date: October 17, 2025*

---

## ✅ **Commit Status**: COMPLETED

**Commit Hash**: `34f6e49`
**Files Changed**: 119 files (40,019 insertions, 5,951 deletions)
**Status**: ✅ All changes committed successfully

```bash
git log -1 --oneline
# 34f6e49 Phase 1: Core features ready for staging deployment
```

---

## ⚠️ **Prerequisites for Deployment**

Before deploying, you need to configure:

### 1. **Database Setup** (Required)

**Option A: PostgreSQL (Production)**
```bash
# Start PostgreSQL if not running
# Create database and user
psql -U postgres
CREATE DATABASE openlearn;
CREATE USER openlearn WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE openlearn TO openlearn;
\q

# Update backend/.env with correct credentials
DATABASE_URL=postgresql+asyncpg://openlearn:your_secure_password@localhost:5432/openlearn
```

**Option B: SQLite (Testing)**
```bash
# For quick testing, use SQLite
cd backend
echo "DATABASE_URL=sqlite+aiosqlite:///./test.db" > .env
```

### 2. **Environment Configuration**

**Backend (`backend/.env`)**:
```bash
# Required
DATABASE_URL=postgresql+asyncpg://openlearn:password@localhost:5432/openlearn
SECRET_KEY=your-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional (for Phase 1)
ELASTICSEARCH_URL=http://localhost:9200  # Not required for Phase 1
REDIS_URL=redis://localhost:6379        # Not required for Phase 1
ENABLE_SCHEDULER=false                   # Disabled in Phase 1
```

**Frontend (`frontend/.env.local`)**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 **Deployment Steps**

### Step 1: Configure Database

Choose one of the database options above and configure accordingly.

### Step 2: Run Database Migrations

```bash
cd backend
# Install alembic if needed
pip install alembic

# Run migrations
alembic upgrade head
```

### Step 3: Build Frontend

```bash
cd frontend
npm run build
```

**Expected Output**:
```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (14/14)
✓ Finalizing page optimization
```

### Step 4: Start Backend Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output**:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Start Frontend Server

```bash
# In a new terminal
cd frontend
npm run start
```

**Expected Output**:
```
✓ Starting...
✓ Ready on http://localhost:3000
```

---

## ✅ **Validation Tests**

Once both servers are running, run these validation tests:

### 1. Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Expected: {"status": "healthy", ...}

# Database health
curl http://localhost:8000/health/database

# Expected: {"status": "healthy", "database": "connected", ...}
```

### 2. API Documentation

Open browser: http://localhost:8000/docs

**Expected**: Swagger UI with all Phase 1 endpoints

### 3. User Registration

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@openlearn.co",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'
```

**Expected**:
```json
{
  "id": "...",
  "email": "test@openlearn.co",
  "full_name": "Test User",
  "is_active": true,
  "created_at": "..."
}
```

### 4. Login

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@openlearn.co&password=TestPassword123!"
```

**Expected**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 5. Frontend Load

Open browser: http://localhost:3000

**Expected**: Dashboard page loads successfully

---

## 🔧 **Troubleshooting**

### Backend Won't Start

**Issue**: "password authentication failed"
**Solution**:
1. Check DATABASE_URL in `backend/.env`
2. Verify PostgreSQL is running: `pg_isready`
3. Try SQLite for testing: `DATABASE_URL=sqlite+aiosqlite:///./test.db`

**Issue**: "Module not found"
**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Won't Start

**Issue**: "prerender-manifest.json not found"
**Solution**:
```bash
cd frontend
npm run build
npm run start
```

**Issue**: "Cannot find module"
**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Port Already in Use

**Issue**: "Address already in use"
**Solution**:
```bash
# Find process using port 8000 or 3000
lsof -i :8000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

---

## 📊 **Expected Performance Metrics**

After successful deployment:

| Metric | Target | Notes |
|--------|--------|-------|
| Backend startup | <10s | Including database connection |
| Frontend startup | <5s | After build complete |
| Health check latency | <50ms | /api/health endpoint |
| Auth latency | <200ms | Registration/login |
| Page load time | <2s | Initial dashboard load |

---

## 🎯 **Phase 1 Active Features**

### Backend APIs
- ✅ `/api/auth/*` - Authentication
- ✅ `/api/health/*` - Health monitoring
- ✅ `/api/scraping/*` - Web scraping
- ✅ `/api/analysis/*` - NLP analysis
- ✅ `/api/preferences/*` - User preferences
- ✅ `/api/avatars/*` - Avatar upload

### Frontend Pages
- ✅ `/` - Dashboard
- ✅ `/preferences` - User settings
- ✅ `/sources` - Data sources
- ✅ `/reset-password` - Password recovery

---

## 🚫 **Disabled Features (Phase 2-3)**

These features are temporarily disabled:
- ❌ Language learning API
- ❌ Task scheduler
- ❌ Notifications
- ❌ Search (Elasticsearch)
- ❌ Data export
- ❌ Batch processing

---

## 📝 **Next Steps After Successful Deployment**

1. ✅ Verify all validation tests pass
2. ⏭️ Monitor logs for 1 hour
3. ⏭️ Run load testing (optional)
4. ⏭️ Document any issues
5. ⏭️ Production deployment decision

---

## 🔐 **Security Notes**

### Before Production:
- [ ] Change `SECRET_KEY` to secure random value (min 32 characters)
- [ ] Update database credentials
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Review security headers
- [ ] Remove test users
- [ ] Enable rate limiting
- [ ] Set up monitoring/logging

---

## 📞 **Support Resources**

### Documentation
- **Phase 1 Summary**: `docs/PHASE_1_COMPLETE.md`
- **Deployment Summary**: `docs/PHASE_1_DEPLOYMENT_SUMMARY.md`
- **API Docs**: http://localhost:8000/docs (when running)

### Scripts
- `scripts/deployment/validate-deployment.sh` - Validation tests
- `scripts/deployment/run-load-tests.sh` - Load testing
- `k8s/deployment.yaml` - Kubernetes config

---

## ✅ **Deployment Checklist**

### Pre-Deployment
- [x] Code committed to git
- [ ] Database configured
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Database migrations run
- [ ] Frontend built

### Deployment
- [ ] Backend server started
- [ ] Frontend server started
- [ ] Health checks passing
- [ ] API documentation accessible

### Post-Deployment
- [ ] User registration works
- [ ] Login/logout functional
- [ ] All endpoints responding
- [ ] No errors in logs
- [ ] Performance acceptable

---

**Deployment Status**: ⏳ **READY** (pending database setup)

*Once database is configured, deployment can proceed immediately.*

**Last Updated**: October 17, 2025
**Version**: 1.0.0-phase1
