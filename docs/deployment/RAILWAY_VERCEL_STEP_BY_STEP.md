# 🎯 Railway + Vercel Deployment - Step-by-Step
**YOUR EXACT ACTIONS - Follow This Precisely**

Total time: **15 minutes**
Cost: **FREE** (using free tiers)

---

## 📋 **Before You Start** (Gather These)

- [ ] GitHub account (you have this)
- [ ] Railway account (you have this)
- [ ] Vercel account (you have this)
- [ ] Supabase account (you have this)
- [ ] SendGrid account (free signup if you don't have)
- [ ] Code pushed to GitHub

---

## 🗂️ **STEP 0: Push Code to GitHub** (2 minutes)

**If not already on GitHub**:

```bash
# On YOUR computer:
cd C:\Users\brand\Development\Project_Workspace\active-development\open_learn

# Initialize Git (if needed)
git remote -v
# If no remote shown, add one:
# git remote add origin https://github.com/YOUR_USERNAME/open_learn.git

# Push all commits
git push -u origin main

# Verify
# Go to https://github.com/YOUR_USERNAME/open_learn
# Should see all your code
```

**If already on GitHub**: Skip to Step 1!

---

## 🗄️ **STEP 1: Deploy Database** (Supabase - 3 minutes)

### **1.1 Create Project**:
```
URL: https://app.supabase.com

Actions:
1. Click "New project"
2. Organization: [Your account]
3. Name: openlearn-production
4. Database Password: [Click "Generate" button]
   ⚠️ COPY THIS PASSWORD TO NOTEPAD NOW!
5. Region: East US 1
6. Click "Create new project"
7. Wait 2 minutes (get coffee ☕)
```

### **1.2 Get Connection String**:
```
When project is ready (green checkmark):

1. Click "Settings" (left sidebar, gear icon)
2. Click "Database"
3. Find "Connection string" section
4. Copy "URI" format
5. PASTE IN NOTEPAD:

postgresql://postgres:YOUR_GENERATED_PASSWORD@db.abcdefghijklmnopqr.supabase.co:5432/postgres

You'll need this in Step 2!
```

### **1.3 Run Migration** (Add timezone columns):
```
1. Click "SQL Editor" (left sidebar)
2. Click "New query"
3. Open on YOUR computer:
   backend/database/migrations/003_add_user_timezone_preferences.sql
4. Copy entire contents
5. Paste into Supabase SQL Editor
6. Click "Run" button
7. Should see: "Success. No rows returned"

✅ Migration applied!
```

---

## 🚂 **STEP 2: Deploy Backend** (Railway - 5 minutes)

### **2.1 Create Railway Project**:
```
URL: https://railway.app

Actions:
1. Click "New Project"
2. Click "Deploy from GitHub repo"
3. If first time: Click "Login with GitHub" and authorize
4. Search for: open_learn
5. Click your repository
6. Railway starts building immediately!

Wait 3-5 minutes for first build
You'll see logs scrolling: "Installing dependencies..."
```

### **2.2 Configure Build** (Set root to backend folder):
```
While build is running:

1. Click "Settings" tab
2. Find "Root Directory"
3. Change from: (empty)
   To: backend
4. Click checkmark to save

5. Find "Start Command"
6. Enter: uvicorn app.main:app --host 0.0.0.0 --port $PORT

7. Find "Healthcheck Path"
8. Enter: /health

Railway will rebuild with new settings
```

### **2.3 Add Environment Variables**:
```
1. Click "Variables" tab
2. Click "Raw Editor"
3. COPY THIS TEMPLATE (replace YOUR_ values):
```

```bash
ENVIRONMENT=production
DEBUG=false

# Generate this on YOUR machine: python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=YOUR_GENERATED_64_CHAR_KEY_HERE

# From Supabase Step 1.2
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres

# Will update after Vercel deployment
FRONTEND_URL=https://openlearn.vercel.app

# Will update after Vercel deployment
CORS_ORIGINS=https://openlearn.vercel.app

# From SendGrid (get in Step 2.4)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=YOUR_SENDGRID_KEY_HERE

ALERT_EMAIL_FROM=OpenLearn <noreply@openlearn.co>
ALERT_EMAIL_TO=YOUR_EMAIL@gmail.com

PYTHONUNBUFFERED=1
PYTHONPATH=/app/backend
```

```
4. Click outside editor to save
5. Railway will redeploy automatically
```

### **2.4 Get SendGrid Key** (if you don't have one):
```
1. https://sendgrid.com → Sign up (free)
2. Settings → API Keys → Create API Key
3. Name: Railway Production
4. Permission: Mail Send (Full Access)
5. Create & View
6. COPY: SG.xxxxxxxxxxxxxxxxxxxxxxx
7. Paste in Railway variables as SMTP_PASSWORD
8. Save

Verify sender:
1. Settings → Sender Authentication
2. Single Sender Verification
3. Add: noreply@openlearn.co
4. Verify email when SendGrid sends it
```

### **2.5 Add Redis** (optional but recommended):
```
1. Railway project → Click "New"
2. Click "Database"
3. Select "Add Redis"
4. Wait 30 seconds

5. Go back to your backend service
6. Variables → Add new variable:
   Name: REDIS_URL
   Value: ${{Redis.REDIS_URL}}

Railway automatically injects the Redis connection!
```

### **2.6 Get Your Backend URL**:
```
1. Railway → Your service → "Settings"
2. Scroll to "Domains"
3. Click "Generate Domain"
4. You get: openlearn-production.up.railway.app

5. COPY THIS URL TO NOTEPAD
   You need it for Vercel!

6. Test it works:
   Open: https://openlearn-production.up.railway.app/health
   Should show: {"status":"healthy"}
```

**✅ Backend live at Railway!**

---

## 🎨 **STEP 3: Deploy Frontend** (Vercel - 5 minutes)

### **3.1 Create Vercel Project**:
```
URL: https://vercel.com

Actions:
1. Click "Add New..." → "Project"
2. If first time: "Continue with GitHub" and authorize
3. Find repository: open_learn
4. Click "Import"
```

### **3.2 Configure Project**:
```
Framework Preset: Next.js ✅ (auto-detected)

Root Directory: frontend

Build Command: npm run build

Output Directory: .next

Install Command: npm install
```

### **3.3 Add Environment Variables**:
```
Click "Environment Variables"

Add Variable 1:
  Name: NEXT_PUBLIC_API_URL
  Value: https://openlearn-production.up.railway.app
         (YOUR Railway URL from Step 2.6)
  Environment: Production, Preview, Development
  Click "Add"

Add Variable 2:
  Name: NODE_ENV
  Value: production
  Environment: Production
  Click "Add"
```

### **3.4 Deploy**:
```
1. Click "Deploy"
2. Vercel builds your app (2-3 minutes)
3. You'll see:
   - "Building..."
   - "Deploying..."
   - "Success!"

4. Click "Visit" or copy URL:
   https://openlearn.vercel.app
```

**✅ Frontend live on Vercel!**

---

## 🔗 **STEP 4: Connect Frontend ↔ Backend** (2 minutes)

### **4.1 Update Railway with Vercel URL**:
```
1. Go to Railway → Your backend service
2. Click "Variables"
3. Edit:
   FRONTEND_URL=https://openlearn.vercel.app
   CORS_ORIGINS=https://openlearn.vercel.app

4. Save
5. Railway redeploys (1 minute)
```

### **4.2 Test Connection**:
```
1. Open: https://openlearn.vercel.app
2. Press F12 (open Developer Tools)
3. Go to "Console" tab
4. Try to sign up or log in
5. Watch network requests

Should see:
✅ Requests to: https://openlearn-production.up.railway.app/api/...
✅ Status: 200 OK
❌ NO CORS errors
```

**If you see CORS errors**:
```
Railway → Variables → Check:
CORS_ORIGINS=https://openlearn.vercel.app

Should match EXACTLY your Vercel URL (no trailing slash!)
```

**✅ Everything connected!**

---

## 🎊 **COMPLETE - YOU'RE LIVE!**

Your platform is now running at:
- **Frontend**: https://openlearn.vercel.app
- **Backend**: https://openlearn-production.up.railway.app
- **Database**: Supabase (automatic backups)
- **Email**: SendGrid (100/day free)

**Test everything**:
1. Open https://openlearn.vercel.app
2. Click "Sign Up"
3. Create account
4. Check email inbox (should receive welcome email)
5. Log in
6. Browse dashboard
7. Test all features

**If all works**: 🎉 **LAUNCH SUCCESSFUL!**

---

## 🔍 **Troubleshooting**

### **Frontend won't connect to backend**:
```
Error in browser console: "Failed to fetch" or CORS error

Fix:
1. Verify Railway backend is running:
   https://YOUR-RAILWAY-URL.up.railway.app/health
   Should return: {"status":"healthy"}

2. Check Vercel environment variable:
   NEXT_PUBLIC_API_URL should match Railway URL EXACTLY

3. Check Railway CORS:
   CORS_ORIGINS should include Vercel URL

4. Redeploy both:
   - Railway: Deployments → Redeploy
   - Vercel: Deployments → Redeploy
```

### **Database connection errors**:
```
Railway logs show: "could not connect to database"

Fix:
1. Verify Supabase connection string is correct
2. Check password has no special characters that need escaping
3. Test connection from Railway:
   Railway → Your service → Shell
   > python
   >>> from sqlalchemy import create_engine
   >>> engine = create_engine("YOUR_DATABASE_URL")
   >>> engine.connect()
   Should succeed
```

### **Emails not sending**:
```
Railway logs show: "SMTP authentication failed"

Fix:
1. Verify SendGrid API key is correct (starts with SG.)
2. Verify sender email is verified in SendGrid
3. Check SendGrid dashboard for send attempts
4. Restart Railway service: Deployments → Redeploy
```

---

## 💰 **Cost Optimization Tips**

### **Stay on Free Tier** (for MVP):
```
Supabase Free:
- 500MB database (good for 50,000+ articles)
- Upgrade only when >400MB

Railway:
- $5 trial credit
- Monitor usage: Dashboard → Usage
- Optimize before paying (reduce wake-ups, optimize queries)

Vercel Free:
- Unlimited bandwidth!
- 100 deployments/day
- Commercial use allowed
- Stay free until you need team features

SendGrid Free:
- 100 emails/day
- Perfect for password resets
- Upgrade to $15/month when you need more
```

### **When to Upgrade**:
```
Supabase → Pro ($25):
- Database >500MB
- Need read replicas
- Want daily backups >7 days

Railway → $5-20/month:
- App running 24/7
- Need more CPU/memory
- Multiple services

Vercel → Pro ($20):
- Need team collaboration
- Want advanced analytics
- Need password protection

Usually Month 3-6 after launch
```

---

## 🎓 **What Each Platform Does**

### **Supabase = Your Database**:
```
Stores:
- User accounts (email, password hashes)
- Articles (scraped news content)
- Vocabulary (learning data)
- Learning sessions (progress tracking)
- Notifications

Features:
- PostgreSQL 15 (latest)
- Automatic backups
- SQL editor
- Real-time subscriptions (websockets)
- Built-in auth (alternative to your JWT system)
```

### **Railway = Your Backend**:
```
Runs:
- FastAPI server (Python)
- API endpoints (/api/auth, /api/articles, etc.)
- Scheduler (scraping jobs)
- NLP processing

Features:
- Automatic scaling
- Docker containers (managed)
- Redis add-on
- Health checks
- Automatic deployments
- Logs & metrics
```

### **Vercel = Your Frontend**:
```
Serves:
- Next.js React app
- Static files (images, CSS, JS)
- Server-side rendering (SSR)

Features:
- Global CDN (fast worldwide)
- Automatic SSL
- Preview deployments
- Analytics
- Serverless functions
- Edge network
```

---

## 🚀 **After Deployment Checklist**

```
Supabase:
[ ] Project created
[ ] Password saved
[ ] Connection string copied
[ ] Migration 003 run successfully
[ ] Can connect from Railway (check Railway logs)

Railway:
[ ] Project deployed
[ ] Environment variables configured
[ ] SECRET_KEY generated (64 chars)
[ ] DATABASE_URL from Supabase
[ ] SMTP credentials from SendGrid
[ ] Health check passing: /health returns {"status":"healthy"}
[ ] Logs show: "Uvicorn running on"
[ ] Domain generated: xxx.up.railway.app

Vercel:
[ ] Project deployed
[ ] Root directory: frontend
[ ] NEXT_PUBLIC_API_URL set to Railway URL
[ ] Build successful
[ ] Site accessible: xxx.vercel.app
[ ] No CORS errors in console
[ ] Can register user (tests backend connection)
[ ] Can login (tests auth flow)

Email:
[ ] SendGrid account created
[ ] API key generated
[ ] Sender email verified
[ ] Password reset email arrives in inbox
[ ] Email has correct reset link (points to Vercel URL)

Overall:
[ ] Homepage loads: https://openlearn.vercel.app
[ ] Backend healthy: https://xxx.up.railway.app/health
[ ] Database accessible (user registration works)
[ ] Emails sending (password reset works)
[ ] No errors in any logs
```

---

## 🎉 **SUCCESS!**

If all checkboxes are checked: **YOU'RE LIVE!**

Your platform is:
- 🌐 Accessible worldwide
- ⚡ Fast (global CDN)
- 🔒 Secure (HTTPS everywhere)
- 📧 Sending emails
- 💾 Backing up automatically
- 📊 Monitored (built-in dashboards)
- 🔄 Auto-deploying (every git push)

**And you didn't manage a single server!** 🎊

---

## 📱 **Share Your Platform**

```
Production URL: https://openlearn.vercel.app
API Docs: https://xxx.up.railway.app/docs
Status: https://xxx.up.railway.app/health

Share with:
- Friends for beta testing
- Social media
- Product Hunt
- Reddit communities
- Colombian language learners
```

---

## 🔄 **Updating Your Platform**

**It's automatic!**

```bash
# Make changes on your computer
cd C:\Users\brand\Development\Project_Workspace\active-development\open_learn

# Edit code...

# Commit and push
git add .
git commit -m "feat: new awesome feature"
git push

# Railway detects push → Rebuilds backend → Deploys (3 min)
# Vercel detects push → Rebuilds frontend → Deploys (2 min)

# Done! Changes live in 5 minutes.
```

**No SSH, no Docker commands, no server access needed!**

---

## 🎯 **What's Next?**

1. **Test thoroughly** (all user flows)
2. **Set up monitoring**:
   - Railway alerts (Settings → Notifications)
   - Vercel alerts (automatic)
   - UptimeRobot (external monitoring)
3. **Announce launch** (social media, email list)
4. **Gather feedback** (first users)
5. **Iterate** (add features based on usage)

**You're live - go celebrate!** 🚀🎉
