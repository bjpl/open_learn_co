# Railway Environment Variables Configuration
**OpenLearn Colombia Backend - Railway Deployment**

Copy these variables to Railway → Your Service → Variables → Raw Editor

---

## 🔐 **Copy This Template** (Update values marked with `YOUR_`)

```bash
# ══════════════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════════════
ENVIRONMENT=production
DEBUG=false
APP_NAME=OpenLearn Colombia
APP_VERSION=1.0.0

# ══════════════════════════════════════════════════
# SECURITY (GENERATE SECRET_KEY - See below)
# ══════════════════════════════════════════════════
SECRET_KEY=YOUR_GENERATED_64_CHARACTER_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ══════════════════════════════════════════════════
# DATABASE (FROM SUPABASE)
# ══════════════════════════════════════════════════
# Get from: Supabase → Settings → Database → Connection string
DATABASE_URL=postgresql://postgres:YOUR_SUPABASE_PASSWORD@db.xxx.supabase.co:5432/postgres

# Individual components (Railway needs these too)
POSTGRES_HOST=db.xxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_SUPABASE_PASSWORD
POSTGRES_DB=postgres

# Connection pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
DB_ECHO=false

# ══════════════════════════════════════════════════
# REDIS (RAILWAY MANAGED - USE REFERENCE)
# ══════════════════════════════════════════════════
# After adding Redis database in Railway:
# Use: ${{Redis.REDIS_URL}} (Railway auto-injects)
REDIS_URL=${{Redis.REDIS_URL}}

# If not using Railway Redis, use Upstash (free tier):
# REDIS_URL=redis://default:YOUR_UPSTASH_PASSWORD@us1-xxx.upstash.io:6379

# ══════════════════════════════════════════════════
# FRONTEND (VERCEL URL)
# ══════════════════════════════════════════════════
FRONTEND_URL=https://openlearn.vercel.app
CORS_ORIGINS=https://openlearn.vercel.app,https://openlearn.co
CORS_ALLOW_CREDENTIALS=true

# ══════════════════════════════════════════════════
# EMAIL (SENDGRID)
# ══════════════════════════════════════════════════
# Get from: SendGrid → Settings → API Keys
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=YOUR_SENDGRID_API_KEY_SG.xxxxxx
ALERT_EMAIL_FROM=OpenLearn Colombia <noreply@openlearn.co>
ALERT_EMAIL_TO=YOUR_ADMIN_EMAIL@gmail.com

# ══════════════════════════════════════════════════
# PYTHON RUNTIME (Railway specific)
# ══════════════════════════════════════════════════
PYTHONUNBUFFERED=1
PYTHONPATH=/app/backend

# ══════════════════════════════════════════════════
# OPTIONAL: Search (Elasticsearch alternative)
# ══════════════════════════════════════════════════
# For MVP, you can skip Elasticsearch
# Or use Railway add-on when needed

# ══════════════════════════════════════════════════
# OPTIONAL: Monitoring
# ══════════════════════════════════════════════════
# Sign up at sentry.io for free error tracking
SENTRY_DSN=YOUR_SENTRY_DSN_IF_YOU_HAVE_ONE
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# ══════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════
LOG_LEVEL=INFO
LOG_FORMAT=json

# ══════════════════════════════════════════════════
# API CONFIGURATION
# ══════════════════════════════════════════════════
API_V1_PREFIX=/api/v1
ALLOWED_HOSTS=*
```

---

## 🔑 **How to Generate Values**

### **SECRET_KEY** (64 characters):
```bash
# On your local machine:
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Example output:
# xR7nK9mP2wQ8fJ4hS6vB1zA5yC3tD0eL7gN9pM2qW8fK4jH6sV1bZ3aC5tE0dR7nK9mP2wQ8fJ4h

# Copy and paste as SECRET_KEY value
```

### **Database URL** (from Supabase):
```
1. Supabase Dashboard → Settings → Database
2. Under "Connection string" section
3. Copy "URI" format
4. Looks like: postgresql://postgres:ABC123xyz@db.xxx.supabase.co:5432/postgres
```

### **Redis URL** (Railway managed):
```
1. In Railway project, click "New"
2. Select "Database" → "Redis"
3. Wait 30 seconds for provisioning
4. In your backend service variables:
   REDIS_URL=${{Redis.REDIS_URL}}
   (Railway will inject the actual URL automatically)
```

### **SendGrid API Key**:
```
1. SendGrid Dashboard → Settings → API Keys
2. Create API Key (Mail Send permission)
3. Copy the key: SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## ⚙️ **Railway Build Configuration**

Railway should auto-detect Python and build correctly. If not:

**Settings → Build**:
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Settings → Deploy**:
- **Healthcheck Path**: `/health`
- **Healthcheck Timeout**: 100
- **Restart Policy**: ON_FAILURE

---

## 🔧 **Troubleshooting Railway**

### **Issue: Build Fails**

**Check Build Logs**:
```
Railway → Deployments → Latest → View Logs

Common issues:
1. "requirements.txt not found"
   → Fix: Set Root Directory to "backend"

2. "Module not found"
   → Fix: Check all dependencies in requirements.txt
   → Add missing: pip freeze > requirements.txt

3. "Database connection failed"
   → Fix: Check DATABASE_URL is correct Supabase URL
```

### **Issue: Health Check Failing**

```
1. Check: /health endpoint exists
   → Should be in backend/app/main.py

2. Verify path: /health (not /api/health)

3. Check logs for errors:
   Railway → Logs → Filter: ERROR

4. Test locally first:
   cd backend
   uvicorn app.main:app
   curl http://localhost:8000/health
```

### **Issue: CORS Errors**

```
Frontend shows: "Access to fetch blocked by CORS policy"

Fix:
1. Railway Variables → Add:
   CORS_ORIGINS=https://openlearn.vercel.app

2. Make sure app/main.py has:
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_ORIGINS,
       allow_credentials=True,
   )
```

---

## 🎯 **Railway Deployment Checklist**

```
Railway Setup:
[ ] Project created from GitHub repo
[ ] Environment variables configured (all required variables)
[ ] SECRET_KEY generated (64 characters)
[ ] Supabase DATABASE_URL added
[ ] Redis database added (optional)
[ ] SendGrid SMTP credentials added
[ ] FRONTEND_URL set to Vercel URL
[ ] Build settings configured (backend root, uvicorn command)
[ ] Health check configured (/health endpoint)
[ ] First deployment successful (check logs for "Uvicorn running")
[ ] Domain generated (xxx.up.railway.app)
[ ] Custom domain added (optional)

Testing:
[ ] Health endpoint accessible: https://xxx.up.railway.app/health
[ ] API docs accessible: https://xxx.up.railway.app/docs
[ ] No CORS errors in browser console
[ ] Database connection working (can register users)
[ ] Email sending working (password reset arrives)
```

---

## 💰 **Railway Pricing**

**Hobby Plan** ($5/month):
- 500 hours of compute (enough for 1 always-on service)
- $5 credit each month
- After credit used: $0.000231/minute ($10/month if always running)

**Free Trial**:
- $5 credit (one-time)
- Perfect for testing deployment
- Upgradde when ready for production

**Recommendation**: Start with free trial, upgrade when you launch.

---

## 🔄 **Deploying Updates**

**Automatic Deployment** (Zero effort!):
```
1. Make changes locally
2. Git commit
3. Git push to GitHub
4. Railway automatically:
   - Detects changes
   - Rebuilds backend
   - Deploys new version
   - Runs health checks
5. Done! (usually <5 minutes)
```

**Manual Trigger**:
```
Railway → Deployments → New Deployment → Deploy
```

**Rollback**:
```
Railway → Deployments → Previous deployment → Redeploy
```

---

## 📊 **Railway Monitoring**

**Built-in Metrics**:
```
Railway Dashboard shows:
- CPU usage
- Memory usage
- Network traffic
- Request rate
- Response time
- Error rate

All automatic, no configuration needed!
```

**View Logs**:
```
Railway → Your Service → Logs
- Real-time log streaming
- Filter by level (INFO, ERROR, etc.)
- Search logs
- Download logs
```

**Set Up Alerts** (optional):
```
Railway → Settings → Notifications
- Deploy success/failure
- Service crashes
- Resource limits
- Send to email or Slack
```

---

## 🎓 **Railway-Specific Features**

### **Automatic HTTPS**
- Every Railway app gets free SSL
- Format: xxx.up.railway.app
- Certificate auto-renews
- No configuration needed

### **Environment Variables from Services**
```bash
# Reference other Railway services:
REDIS_URL=${{Redis.REDIS_URL}}
POSTGRES_URL=${{Postgres.DATABASE_URL}}

# Railway injects actual URLs automatically
```

### **Automatic Rollback**
- If deployment fails health check
- Railway automatically rolls back to previous version
- Zero downtime

### **Horizontal Scaling** (future):
```
Settings → Scaling
- Add replicas (multiple instances)
- Load balancer automatic
- Pay per instance
```

---

## 🚀 **Next Steps After Railway Deployment**

1. ✅ Backend deployed to Railway
2. ➡️ **Next**: Deploy frontend to Vercel (Part 3)
3. ➡️ **Then**: Connect Railway ↔ Vercel
4. ➡️ **Finally**: Test complete system

Continue to **VERCEL_ENV.md** for frontend deployment →
