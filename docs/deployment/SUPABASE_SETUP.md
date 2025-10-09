# Supabase Database Setup Guide
**OpenLearn Colombia - Managed PostgreSQL Database**

---

## 🎯 Why Supabase?

**vs Self-Hosted PostgreSQL**:
- ✅ No server maintenance
- ✅ Automatic backups (daily)
- ✅ Free tier (500MB database)
- ✅ Built-in dashboard for SQL queries
- ✅ Connection pooling automatic
- ✅ SSL enforced
- ✅ Point-in-time recovery
- ✅ Read replicas (paid plans)

**Costs**:
- **Free Tier**: 500MB database, 2 CPU, 1GB RAM (perfect for MVP)
- **Pro**: $25/month (8GB database, 4 CPU, 4GB RAM)

---

## 🚀 **Setup Steps** (3 Minutes)

### **Step 1: Create Supabase Project**

```
1. Go to: https://app.supabase.com

2. Sign in with GitHub

3. Click "New project"

4. Fill in:
   - Organization: Your account
   - Name: openlearn-production
   - Database Password: [Click "Generate" - COPY THIS PASSWORD!]
   - Region: East US (or closest to your users)
   - Plan: Free (or Pro if you want more resources)

5. Click "Create new project"

6. Wait 2 minutes for provisioning
   - You'll see a progress bar
   - "Setting up your project..."
   - "Connecting to database..."

7. When complete, you'll see the dashboard
```

**⚠️ CRITICAL**: Save the database password! You can't retrieve it later.

---

### **Step 2: Get Connection String**

```
1. Click "Settings" (gear icon in sidebar)

2. Click "Database"

3. Scroll to "Connection string" section

4. Copy "URI" format:
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres

5. SAVE THIS - you need it for:
   - Railway environment variables
   - Local development .env
   - Database migrations
```

**Connection String Explained**:
```
postgresql://postgres:abc123@db.xxx.supabase.co:5432/postgres
           │   │      │       │                │     │
           │   │      │       │                │     └─ Database name
           │   │      │       │                └─────── Port (always 5432)
           │   │      │       └──────────────────────── Your unique Supabase host
           │   │      └──────────────────────────────── Your password
           │   └─────────────────────────────────────── Username (always "postgres")
           └─────────────────────────────────────────── Protocol
```

---

### **Step 3: Run Database Migrations**

**Option A: Using Supabase SQL Editor** (Easiest):
```
1. Supabase Dashboard → SQL Editor

2. Click "New query"

3. Copy contents of your migration file:
   backend/database/migrations/003_add_user_timezone_preferences.sql

4. Paste into SQL Editor

5. Click "Run" (or Cmd+Enter)

6. Should see:
   "Success. No rows returned"
   or
   "ALTER TABLE" success messages

7. Verify in Table Editor:
   - Click "Table Editor"
   - Select "users" table
   - Should see columns: timezone, language, preferred_categories
```

**Option B: Using psql** (from your local machine):
```bash
# Install PostgreSQL client if needed:
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt install postgresql-client

# Connect to Supabase
psql "postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres"

# Should see:
# psql (14.0, server 15.1)
# SSL connection
# postgres=>

# Run migration
\i backend/database/migrations/003_add_user_timezone_preferences.sql

# Should see:
# ALTER TABLE
# ALTER TABLE
# CREATE INDEX
# UPDATE 0

# Verify
\d users
# Should show timezone and language columns

# Exit
\q
```

**Option C: Railway Runs Migration Automatically**:
```
After Railway backend starts, it can run migrations automatically.

Add to Railway variables:
RUN_MIGRATIONS_ON_START=true

And add startup script:
"start": "alembic upgrade head && uvicorn app.main:app"
```

---

## 🔐 **Security Configuration**

### **Enable Row Level Security** (Optional for multi-tenant):
```sql
-- In Supabase SQL Editor

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only access their own data
CREATE POLICY user_access_own_data ON users
  FOR ALL
  USING (auth.uid() = id);
```

### **Connection Pooling** (Automatic):
```
Supabase provides connection pooling by default:
- Mode: Transaction
- Max connections: 100 (Free), 400 (Pro)
- Perfect for Railway (serverless-friendly)
```

### **SSL/TLS** (Always Enabled):
```
All Supabase connections use SSL by default.
- TLS 1.2+
- Certificate auto-rotates
- No configuration needed
```

---

## 📊 **Supabase Dashboard Features**

### **Table Editor**:
```
Visual database editor:
- View tables as spreadsheet
- Add/edit/delete rows
- Filter and search data
- Export to CSV
- Import from CSV

Perfect for:
- Checking user registrations
- Debugging data issues
- Manual data entry
- Quick queries
```

### **SQL Editor**:
```
Write and save SQL queries:
- Syntax highlighting
- Auto-complete
- Save favorite queries
- Share queries with team

Useful for:
- Running migrations
- Analytics queries
- Data exports
- Database maintenance
```

### **Database Logs**:
```
View query logs:
- Slow query detection
- Connection statistics
- Error logs
- Real-time monitoring

Monitor:
- Query performance
- Connection pool usage
- Lock contention
- Index usage
```

### **Backups** (Automatic):
```
Free Tier:
- Daily backups (7 day retention)
- Point-in-time recovery (last 7 days)

Pro Tier:
- Daily backups (30 day retention)
- Point-in-time recovery (30 days)
- Download backups
- Automated restore
```

---

## 🧪 **Testing Database Connection**

### **Test from Railway**:
```bash
# Railway → Your Backend → Logs

Should see on startup:
"INFO: Database connection successful"
"INFO: Connected to PostgreSQL at db.xxx.supabase.co"

If errors:
"ERROR: could not connect to server"
→ Check DATABASE_URL in Railway variables
→ Verify Supabase project is running
→ Check password is correct
```

### **Test from Local Development**:
```bash
# On your local machine:
cd backend

# Create .env with Supabase URL
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres

# Test connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('✅ Supabase connection successful!')
"
```

---

## 📈 **Monitoring Database Performance**

### **Query Performance**:
```
Supabase → Reports → Database

View:
- Queries per second
- Average query time
- Slow queries (>100ms)
- Most frequent queries
- Index hit rate (should be >99%)
```

### **Connection Pool Usage**:
```
Supabase → Reports → Database → Connections

Watch:
- Active connections
- Idle connections
- Waiting queries
- Max connections reached?

Healthy:
- Active: <50 (Free tier)
- Idle: <10
- Waiting: 0
```

### **Storage Usage**:
```
Supabase → Settings → Usage

Monitor:
- Database size (500MB limit on free tier)
- Transfer (GB/month)
- Storage API (for file uploads when you add avatars)

Set up alerts:
- Email when database reaches 400MB (80% of free tier)
- Upgrade to Pro before hitting limit
```

---

## 🔄 **Database Maintenance**

### **Weekly Tasks** (5 minutes):
```sql
-- In Supabase SQL Editor

-- Vacuum database (reclaim space)
VACUUM ANALYZE;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check for missing indexes (slow queries)
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1;
```

### **Monthly Tasks** (10 minutes):
```
1. Review slow query log
   → Supabase → Reports → Database → Slow Queries
   → Add indexes for queries >100ms

2. Check database size growth
   → Supabase → Settings → Usage
   → Plan capacity upgrades

3. Review backup retention
   → Supabase → Database → Backups
   → Download important backups to local storage

4. Test backup restore
   → Create test project
   → Restore from backup
   → Verify data integrity
```

---

## 🆘 **Troubleshooting**

### **Issue: "Connection Refused"**

```
Error: FATAL: no pg_hba.conf entry for host

Cause: IP not allowed (Supabase restricts by default)

Fix:
1. Supabase → Settings → Database
2. Scroll to "Connection pooling"
3. Check "Enable connection pooling"
4. Use pooler URL instead of direct:
   postgresql://postgres.xxx:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

### **Issue: "Too Many Connections"**

```
Error: FATAL: remaining connection slots are reserved

Cause: Free tier limited to 60 connections

Fix Option 1 (Reduce connections):
- Railway → Variables
- Add: DB_POOL_SIZE=5
- Add: DB_MAX_OVERFLOW=2

Fix Option 2 (Use pooler):
- Use Supabase connection pooler URL
- Supports 1000+ concurrent connections

Fix Option 3 (Upgrade):
- Supabase → Settings → Billing
- Upgrade to Pro ($25/month)
- 200 direct connections
```

### **Issue: "Database Locked"**

```
Error: database is locked

Cause: Long-running query or transaction

Fix:
1. Supabase → Database → Locks
2. Find blocking query
3. Kill if needed:

SELECT pg_cancel_backend(PID);  -- Graceful cancel
-- or --
SELECT pg_terminate_backend(PID);  -- Force kill
```

---

## 🎓 **Supabase-Specific Features**

### **Real-Time Subscriptions** (future feature):
```typescript
// Listen to database changes in real-time
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Subscribe to new articles
supabase
  .from('scraped_content')
  .on('INSERT', payload => {
    console.log('New article:', payload.new)
    // Update UI automatically
  })
  .subscribe()
```

### **Built-in Authentication** (alternative to your JWT system):
```
Supabase has built-in auth:
- Email/password
- Magic links
- OAuth (Google, GitHub, etc.)
- Row Level Security integration

You could migrate to Supabase Auth in future for:
- Less code to maintain
- Built-in user management UI
- Social login ready
```

### **Storage** (for avatar uploads):
```
Supabase → Storage

- Create bucket: "avatars"
- Set public/private
- Upload from frontend directly
- CDN-backed (fast)
- Automatic image optimization
- Free: 1GB storage

When you add avatar upload:
- Upload directly to Supabase Storage
- No need for S3
- Simpler integration
```

---

## ✅ **Supabase Setup Checklist**

```
Account & Project:
[ ] Supabase account created
[ ] Project created (openlearn-production)
[ ] Region selected (closest to users)
[ ] Database password saved securely

Configuration:
[ ] Connection string copied
[ ] Connection pooling enabled (recommended)
[ ] SSL verified (should be automatic)
[ ] Migration 003 executed
[ ] Tables created (users, scraped_content, etc.)

Integration:
[ ] DATABASE_URL added to Railway
[ ] DATABASE_URL added to local .env
[ ] Connection tested from Railway (check logs)
[ ] Connection tested from local development

Monitoring:
[ ] Dashboard bookmarked
[ ] Usage alerts set up (email when >80% storage)
[ ] Backup schedule verified (daily automatic)
```

---

## 🎊 **Database Ready!**

Your Supabase PostgreSQL database is now:
- ✅ Provisioned and running
- ✅ Accessible from Railway backend
- ✅ Backing up daily automatically
- ✅ Monitored via dashboard
- ✅ SSL-secured
- ✅ Globally distributed (fast from anywhere)

**Next**: Deploy backend to Railway →
