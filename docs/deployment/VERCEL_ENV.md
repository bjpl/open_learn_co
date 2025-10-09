# Vercel Environment Variables Configuration
**OpenLearn Colombia Frontend - Vercel Deployment**

Copy these variables to Vercel → Your Project → Settings → Environment Variables

---

## 🔐 **Environment Variables for Vercel**

### **Required Variables**:

```bash
# ══════════════════════════════════════════════════
# API CONNECTION (FROM RAILWAY)
# ══════════════════════════════════════════════════
# Name: NEXT_PUBLIC_API_URL
# Value: https://openlearn-production.up.railway.app
# (This is your Railway backend URL)

NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_APP_NAME.up.railway.app


# ══════════════════════════════════════════════════
# BUILD ENVIRONMENT
# ══════════════════════════════════════════════════
# Name: NODE_ENV
# Value: production

NODE_ENV=production


# ══════════════════════════════════════════════════
# OPTIONAL: Analytics & Monitoring
# ══════════════════════════════════════════════════
# Vercel Analytics (built-in, free)
# Just enable in Vercel dashboard, no env var needed

# Google Analytics (if you want)
# NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Sentry Frontend Monitoring (if you want)
# NEXT_PUBLIC_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

## ⚙️ **Vercel Build Settings**

**Project Settings → General**:

```
Framework Preset: Next.js
Root Directory: frontend
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Node.js Version: 18.x
```

---

## 🌍 **Domain Configuration**

### **Using Vercel Domain** (Free, Automatic):
```
Your app URL: https://openlearn.vercel.app
- Free SSL certificate
- Global CDN (fast worldwide)
- Auto-renewing certificate
- No configuration needed
```

### **Using Custom Domain** (Optional):
```
1. Vercel Dashboard → Settings → Domains
2. Add domain: openlearn.co
3. Vercel provides DNS instructions:

   In your domain registrar (Namecheap, etc.):

   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   TTL: 300

   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   TTL: 300

4. Save DNS changes
5. Wait 5-30 minutes for propagation
6. Vercel automatically:
   - Provisions SSL certificate
   - Configures HTTPS
   - Enables custom domain
```

---

## 📁 **Frontend Directory Structure**

Vercel needs your Next.js app in `frontend/` directory:

```
open_learn/
├── frontend/              ← Vercel builds from here
│   ├── src/
│   ├── public/
│   ├── package.json      ← Dependencies
│   ├── next.config.js    ← Next.js config
│   └── tsconfig.json     ← TypeScript config
├── backend/              ← (Railway builds this separately)
└── vercel.json           ← Vercel configuration (already created!)
```

**Important**: Set Root Directory to `frontend` in Vercel settings!

---

## 🔧 **API Connection Pattern**

### **How Frontend Connects to Backend**:

```typescript
// frontend/src/lib/api-client.ts (example)

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchAPI(endpoint: string, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  return response.json()
}

// Usage:
const articles = await fetchAPI('/api/v1/articles')
// Fetches from: https://openlearn-production.up.railway.app/api/v1/articles
```

**Environment Variable Flow**:
```
Vercel build time:
  process.env.NEXT_PUBLIC_API_URL
  ↓
  Hardcoded into JavaScript bundle
  ↓
  User's browser makes requests to Railway backend
```

**IMPORTANT**: Variables starting with `NEXT_PUBLIC_` are:
- Embedded in frontend JavaScript
- Visible to users in browser
- Safe for public URLs (don't put secrets here!)

---

## 🧪 **Testing Vercel Deployment**

### **Test Build Locally First**:
```bash
# On your local machine:
cd frontend

# Set environment variable
export NEXT_PUBLIC_API_URL=https://openlearn-production.up.railway.app

# Build
npm run build

# Test production build
npm start

# Open: http://localhost:3000
# Should work without errors
```

### **Test on Vercel**:
```
1. After deployment, check logs:
   Vercel → Deployments → Latest → View Function Logs

2. Should see:
   "Build completed"
   "Build time: 2m 34s"

3. Click "Visit" to open site

4. Open browser console (F12)
   Should NOT see:
   - CORS errors
   - 404 errors for API calls
   - Network errors

5. Test user registration:
   - Should send request to Railway backend
   - Should create user in Supabase database
```

---

## 🔄 **Vercel Deployment Workflow**

### **Automatic Deployments** (Recommended):
```
Production Branch: main
  → Every push to main auto-deploys to production
  → URL: https://openlearn.vercel.app

Preview Branches: feature-*, dev
  → Every push creates preview deployment
  → URL: https://openlearn-git-feature-branch.vercel.app
  → Perfect for testing before production
```

### **Manual Deployment**:
```
Vercel Dashboard → Deployments → Redeploy
```

### **Rollback**:
```
Vercel → Deployments → Previous deployment → Promote to Production
```

---

## 📊 **Vercel Analytics** (Built-in, Free)

Enable in Vercel Dashboard:
```
Settings → Analytics → Enable

Tracks:
- Page views
- Unique visitors
- Top pages
- Traffic sources
- Device types
- Geographic distribution

Real-time dashboard, no code changes needed!
```

---

## 💡 **Vercel Best Practices**

### **Image Optimization**:
```typescript
// Next.js Image component automatically optimizes
import Image from 'next/image'

<Image
  src="/logo.png"
  width={200}
  height={50}
  alt="OpenLearn"
/>

// Vercel automatically:
// - Resizes for device
// - Converts to WebP
// - Lazy loads
// - Serves from CDN
```

### **Caching Headers**:
```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },
}
```

### **Edge Functions** (for fast response):
```typescript
// For pages that need to be fast globally
export const config = {
  runtime: 'edge',
}

// Runs on Vercel's edge network (100+ locations worldwide)
```

---

## 🎯 **Vercel Deployment Checklist**

```
Vercel Configuration:
[ ] Project imported from GitHub
[ ] Framework preset: Next.js (auto-detected)
[ ] Root directory: frontend
[ ] Environment variables added:
    [ ] NEXT_PUBLIC_API_URL (Railway backend URL)
    [ ] NODE_ENV=production
[ ] Build successful (check deployment logs)
[ ] Preview URL working
[ ] Custom domain added (optional)
[ ] SSL certificate active (automatic)

Testing:
[ ] Homepage loads
[ ] API calls succeed (no CORS errors)
[ ] User registration works
[ ] Login works
[ ] Dashboard loads
[ ] Images load (if any)
[ ] No console errors

Performance:
[ ] Lighthouse score >90 (Vercel → Analytics → Lighthouse)
[ ] First Contentful Paint <2s
[ ] Time to Interactive <3s
```

---

## 🚀 **After Vercel Deployment**

Update Railway with your Vercel URL:
```
Railway → Backend Service → Variables

Update:
FRONTEND_URL=https://openlearn.vercel.app
CORS_ORIGINS=https://openlearn.vercel.app

Save → Auto-redeploys
```

---

**Frontend complete!** Next: Test the complete system →
