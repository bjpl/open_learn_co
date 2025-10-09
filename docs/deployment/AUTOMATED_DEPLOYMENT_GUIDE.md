# 🤖 Automated Deployment Guide
**OpenLearn Colombia - Minimal Human Effort Deployment**

---

## 🎯 What This Does For You

This automated deployment package handles **90% of deployment work automatically**:

✅ **Automated**:
- Docker + Docker Compose installation
- Secure credential generation (SECRET_KEY, database passwords)
- Database migration execution
- Application building and startup
- Nginx installation and configuration
- SSL certificate setup (Let's Encrypt)
- Firewall configuration
- Automated backup scheduling
- Health check verification

⚠️ **You Still Need To** (10 minutes):
1. Create server (DigitalOcean, AWS, etc.)
2. Register domain name + configure DNS
3. Create SendGrid account + get API key
4. SSH into server and run ONE command

---

## 🚀 Quick Start (3 Steps!)

### **Step 1: Prerequisites** (15 minutes)

**1.1 Create Server**:
- Go to https://www.digitalocean.com (or AWS, Linode, Hetzner)
- Create account
- Create new Droplet/Server:
  - **OS**: Ubuntu 22.04 LTS
  - **Size**: 2 CPU, 4GB RAM ($12/month)
  - **Datacenter**: Choose closest to your users
  - **Authentication**: Add your SSH key
- Note the IP address (e.g., `123.45.67.89`)

**1.2 Configure DNS**:
- Go to your domain registrar (Namecheap, Google Domains, etc.)
- Add A record:
  ```
  Type: A
  Name: @
  Value: 123.45.67.89 (your server IP)
  TTL: 300
  ```
- Add A record for www:
  ```
  Type: A
  Name: www
  Value: 123.45.67.89
  TTL: 300
  ```
- Wait 5-30 minutes for DNS propagation

**1.3 Get SendGrid API Key**:
- Go to https://sendgrid.com
- Sign up for free account (100 emails/day)
- Navigate to Settings → API Keys
- Create new API key (Mail Send permission)
- Copy the key: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### **Step 2: Upload Code to Server** (2 minutes)

**Option A: Git Clone** (if code is on GitHub):
```bash
# SSH into your server
ssh root@123.45.67.89

# Clone repository
cd /opt
git clone https://github.com/yourusername/open_learn.git
cd open_learn
```

**Option B: SCP Upload** (from your local machine):
```bash
# From Windows (Git Bash or PowerShell):
cd C:\Users\brand\Development\Project_Workspace\active-development\open_learn

# Create tar archive
tar -czf open_learn.tar.gz --exclude=node_modules --exclude=.git --exclude=backend/__pycache__ .

# Upload to server
scp open_learn.tar.gz root@123.45.67.89:/opt/

# SSH into server and extract
ssh root@123.45.67.89
cd /opt
tar -xzf open_learn.tar.gz -C open_learn
cd open_learn
```

---

### **Step 3: Run Automated Deployment** (ONE COMMAND!)

**On the server**:
```bash
# Make script executable
chmod +x scripts/production/quick_deploy.sh

# Run deployment (this does EVERYTHING)
sudo ./scripts/production/quick_deploy.sh
```

**You'll be prompted for**:
- Domain name: `openlearn.co`
- SendGrid API key: `SG.xxxxxxxxxxxx` (paste your key)
- Admin email: `admin@openlearn.co` (or your email)

**Then sit back and watch** (10-20 minutes):
```
🔐 Generating secure credentials...
✅ .env file created

🔧 Running automated deployment...
✅ Docker installed
✅ Docker Compose installed
✅ Database migration complete
✅ Docker images built
✅ All services started
✅ Nginx configured
✅ SSL certificate installed
✅ Firewall configured
✅ Automated backups scheduled

🧪 Running deployment verification...
✅ Backend health check PASS
✅ Frontend responding PASS
✅ Database connection PASS
✅ Redis connection PASS
✅ HTTPS accessible PASS

╔══════════════════════════════════════════════════════════╗
║  🎉 DEPLOYMENT COMPLETE!                                  ║
╚══════════════════════════════════════════════════════════╝

🌐 Access at: https://openlearn.co
```

---

## 🎊 **That's It - You're Live!**

Your platform is deployed and accessible at your domain with:
- ✅ HTTPS (SSL certificate)
- ✅ Email service configured
- ✅ All services running
- ✅ Firewall protecting server
- ✅ Daily backups scheduled
- ✅ Health monitoring active

---

## 📋 **What The Script Did For You**

### **System Setup**
```bash
✅ Installed Docker Engine
✅ Installed Docker Compose v2
✅ Started and enabled Docker service
✅ Configured Docker to start on boot
```

### **Application Deployment**
```bash
✅ Generated SECRET_KEY (64-character cryptographic key)
✅ Generated database password (32-character secure)
✅ Generated Redis password (32-character secure)
✅ Created production .env file
✅ Set .env permissions to 600 (secure)
✅ Started PostgreSQL container
✅ Ran database migration 003 (timezone fields)
✅ Built Docker images (backend + frontend)
✅ Started all services (frontend, backend, postgres, redis, elasticsearch)
✅ Verified all containers healthy
```

### **Web Server**
```bash
✅ Installed Nginx
✅ Copied production Nginx configuration
✅ Enabled OpenLearn site
✅ Disabled default Nginx site
✅ Tested Nginx configuration syntax
✅ Installed Certbot (Let's Encrypt)
✅ Generated SSL certificate for your domain
✅ Configured HTTPS
✅ Set up HTTP → HTTPS redirect
✅ Enabled SSL auto-renewal
✅ Reloaded Nginx with new config
```

### **Security**
```bash
✅ Installed UFW firewall
✅ Configured firewall rules:
   - Allow port 22 (SSH)
   - Allow port 80 (HTTP)
   - Allow port 443 (HTTPS)
   - Block all other ports
✅ Enabled firewall
✅ Added security headers to Nginx
✅ Configured rate limiting (auth endpoints)
```

### **Monitoring & Backups**
```bash
✅ Created backup directory (/backups/openlearn)
✅ Set secure permissions (700)
✅ Installed backup script
✅ Scheduled daily backups (2am via cron)
✅ Ran initial backup
✅ Configured 30-day backup retention
```

### **Verification**
```bash
✅ Tested backend health endpoint
✅ Tested frontend accessibility
✅ Verified database connection
✅ Verified Redis connection
✅ Checked SSL certificate
✅ Verified HTTPS redirect
✅ Checked firewall status
✅ Generated verification report
```

---

## 🔧 **Post-Deployment: What YOU Do**

### **Immediate (5 minutes)**
1. **Test Your Site**:
   ```
   - Open https://openlearn.co in browser
   - Should see: OpenLearn homepage with HTTPS padlock 🔒
   - Click "Sign Up" → Create account
   - Check email for welcome message
   - Log in with new account
   ```

2. **Set Up Monitoring**:
   ```
   - Go to https://uptimerobot.com
   - Create free account
   - Add monitor: https://openlearn.co/health
   - Set alert email: your-email@gmail.com
   ```

### **First Week (Daily Checks - 5 minutes each)**
```bash
# SSH into server
ssh root@your-server-ip

# Check if services are running
cd /opt/open_learn
docker-compose ps
# All should show: Up (healthy)

# Check for errors
docker-compose logs --since 24h | grep ERROR
# Should be: minimal or zero

# Check disk space
df -h /
# Should have: >10GB free

# Check backups
ls -lh /backups/openlearn/
# Should show: daily backup files

# That's it!
```

---

## 🆘 **If Something Goes Wrong**

### **Deployment Script Failed**

**Check which phase failed**:
```bash
# Re-run with verbose output
sudo bash -x scripts/production/quick_deploy.sh 2>&1 | tee deployment.log

# Look for the last successful message before error
# Common issues:

# "Docker installation failed"
→ Check internet connection
→ Try: curl https://google.com

# "Database migration failed"
→ Check if database is running: docker-compose ps postgres
→ Check logs: docker-compose logs postgres

# "SSL certificate failed"
→ Verify DNS: dig openlearn.co (should show your IP)
→ Wait for DNS propagation (5-30 minutes)
→ Try again: sudo certbot --nginx -d openlearn.co
```

### **Site Not Accessible**

**Step-by-step diagnosis**:
```bash
# 1. Check if Nginx running
sudo systemctl status nginx
# Should show: active (running)

# 2. Check if services running
docker-compose ps
# All should show: Up

# 3. Check if DNS configured
dig openlearn.co
# Should show: your server IP in ANSWER section

# 4. Check firewall
sudo ufw status
# Should show: 80/tcp ALLOW, 443/tcp ALLOW

# 5. Test locally first
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# 6. Check Nginx logs
sudo tail -50 /var/log/nginx/openlearn_error.log
# Look for specific errors
```

### **Password Reset Emails Not Sending**

```bash
# 1. Verify SendGrid key in .env
grep SMTP_PASSWORD .env
# Should show: SG.xxxxxxxxxxxxxxx (not placeholder)

# 2. Test SMTP connection
docker-compose exec backend python3 -c "
import smtplib
from app.config.settings import settings
server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
server.starttls()
server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
print('✅ SMTP connection successful')
server.quit()
"

# 3. Check SendGrid dashboard
# Login to sendgrid.com → Activity → Email Activity
# Look for your test emails

# 4. Check backend logs
docker-compose logs backend | grep email
```

---

## 🔄 **Updating Your Deployment**

### **Deploy Code Changes** (5 minutes)
```bash
# SSH into server
ssh root@your-server-ip
cd /opt/open_learn

# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Verify update
curl https://openlearn.co/health
```

### **Update Configuration** (2 minutes)
```bash
# Edit .env
nano .env
# Make your changes

# Restart affected services
docker-compose restart backend  # If backend config changed
docker-compose restart frontend  # If frontend config changed
```

### **Rollback to Previous Version** (3 minutes)
```bash
# View commit history
git log --oneline -10

# Rollback code
git reset --hard <previous-commit-hash>

# Rebuild and restart
docker-compose up -d --build
```

---

## 📊 **What To Monitor**

### **Uptime** (UptimeRobot - Set and Forget)
- ✅ Monitors: https://openlearn.co/health every 5 minutes
- ✅ Alerts via email if site goes down
- ✅ Shows uptime history and response times

### **Logs** (Check Daily)
```bash
# SSH into server
docker-compose logs --since 24h | grep -i "error\|critical"
# Should be: minimal errors
```

### **Resources** (Check Weekly)
```bash
# SSH into server
docker stats --no-stream
# Should show: <50% CPU, <80% memory

df -h
# Should have: >10GB free disk
```

### **Backups** (Check Monthly)
```bash
# List backups
ls -lh /backups/openlearn/
# Should show: ~30 recent backup files

# Test restore (on test database!)
gunzip < /backups/openlearn/db_backup_<latest>.sql.gz | docker-compose exec -T postgres psql -U openlearn_prod -d openlearn_test
```

---

## 🎓 **Understanding What Happened**

### **The Magic Behind One Command**

When you ran `quick_deploy.sh`, here's what happened automatically:

**Minutes 0-2**: System Preparation
```
→ Updated Ubuntu package lists
→ Installed Docker prerequisites
→ Added Docker's GPG key (security verification)
→ Added Docker repository to apt sources
→ Installed Docker Engine (container runtime)
→ Installed Docker Compose (multi-container orchestrator)
```

**Minutes 2-5**: Application Setup
```
→ Generated cryptographically secure SECRET_KEY (64 chars)
→ Generated database password (32 chars, random)
→ Generated Redis password (32 chars, random)
→ Created .env file with all production settings
→ Set file permissions to 600 (owner read/write only)
→ Started PostgreSQL container
→ Waited for database initialization
→ Ran migration 003 (added timezone + language columns)
```

**Minutes 5-15**: Building
```
→ Downloaded Python 3.10 base image
→ Installed Python dependencies (FastAPI, SQLAlchemy, etc.)
→ Downloaded Node 18 base image
→ Installed Node dependencies (Next.js, React, etc.)
→ Compiled TypeScript to JavaScript
→ Built production Next.js bundle
→ Created optimized Docker images
```

**Minutes 15-17**: Startup
```
→ Started PostgreSQL (persistent volume created)
→ Started Redis (in-memory cache)
→ Started Elasticsearch (search index)
→ Started Backend (FastAPI server on port 8000)
→ Started Frontend (Next.js server on port 3000)
→ Waited for all services to be healthy
```

**Minutes 17-18**: Web Server
```
→ Installed Nginx web server
→ Copied production configuration
→ Enabled OpenLearn site
→ Tested configuration syntax
→ Installed Certbot (Let's Encrypt client)
```

**Minutes 18-19**: SSL Certificate
```
→ Contacted Let's Encrypt servers
→ Created challenge file (/.well-known/acme-challenge/)
→ Let's Encrypt verified domain ownership
→ Generated SSL certificate (valid 90 days)
→ Installed certificate in Nginx
→ Configured auto-renewal cron job
→ Reloaded Nginx with HTTPS
```

**Minutes 19-20**: Security
```
→ Installed UFW firewall
→ Allowed port 22 (SSH - so you can still access server)
→ Allowed port 80 (HTTP - for Let's Encrypt + redirects)
→ Allowed port 443 (HTTPS - for users)
→ Blocked all other ports
→ Enabled firewall
```

**Minutes 20-21**: Backups
```
→ Created /backups/openlearn directory
→ Set permissions to 700 (owner only)
→ Installed backup script
→ Scheduled daily cron job (2am)
→ Ran initial backup
→ Verified backup file created
```

**Minutes 21-22**: Verification
```
→ Tested backend health endpoint
→ Tested frontend accessibility
→ Verified database connection
→ Verified Redis connection
→ Checked SSL certificate installation
→ Tested HTTPS redirect
→ Checked firewall status
→ Verified disk space adequate
→ Checked memory usage healthy
→ Generated verification report
```

---

## 🎯 **Your Minimal Effort Checklist**

### **Before Running Script** (15 minutes):
- [ ] Create server ($12/month)
- [ ] Note server IP
- [ ] Register domain name ($10/year)
- [ ] Point DNS to server IP
- [ ] Wait for DNS propagation
- [ ] Create SendGrid account (free)
- [ ] Get API key
- [ ] Upload code to server

### **Running Script** (1 command, 20 minutes wait):
- [ ] SSH into server
- [ ] Run: `sudo ./scripts/production/quick_deploy.sh`
- [ ] Enter domain name when prompted
- [ ] Enter SendGrid key when prompted
- [ ] Enter admin email when prompted
- [ ] Wait for completion

### **After Script** (5 minutes):
- [ ] Open https://your-domain.com in browser
- [ ] Verify HTTPS padlock shows
- [ ] Create test user account
- [ ] Check email inbox for welcome email
- [ ] Test login
- [ ] Set up UptimeRobot monitoring

### **Ongoing** (5 minutes daily first week):
- [ ] Check UptimeRobot shows site is up
- [ ] Verify backups are running (ls /backups/openlearn/)
- [ ] Check for errors (docker-compose logs)

---

## 💰 **Total Cost Breakdown**

**One-Time Costs**:
- Domain name: ~$10/year
- (Optional) Premium email: $0 (SendGrid free tier: 100/day)

**Monthly Costs**:
- Server (DigitalOcean): $12/month (2 CPU, 4GB RAM)
- OR Server (AWS t3.medium): ~$30/month
- OR Server (Hetzner): €5/month (~$5.50)

**Total First Year**:
- Domain: $10
- Server: $144 (DigitalOcean) or $60 (Hetzner)
- **Total: $154 - $70** depending on host

**Scaling Costs** (when you grow):
- More server resources: +$10-50/month per tier
- SendGrid Pro: $15/month (40,000 emails)
- AWS SES: $0.10 per 1,000 emails

---

## 🔧 **Customization Options**

### **Change Domain Later**
```bash
# 1. Update .env
sed -i 's|openlearn.co|newdomain.com|g' .env

# 2. Update Nginx config
sudo sed -i 's|openlearn.co|newdomain.com|g' /etc/nginx/sites-available/openlearn

# 3. Get new SSL certificate
sudo certbot --nginx -d newdomain.com

# 4. Restart services
docker-compose restart
sudo systemctl reload nginx
```

### **Add More Email Volume**
```bash
# Upgrade SendGrid plan or switch to AWS SES

# For AWS SES:
# 1. Get SMTP credentials from AWS
# 2. Update .env:
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_USER=<your-iam-smtp-username>
SMTP_PASSWORD=<your-iam-smtp-password>

# 3. Restart backend
docker-compose restart backend
```

### **Add More Server Resources**
```bash
# On DigitalOcean/AWS/etc dashboard:
# 1. Resize server (2 CPU, 4GB → 4 CPU, 8GB)
# 2. Server will reboot
# 3. SSH back in and verify
docker-compose ps
# All should restart automatically
```

---

## 🎉 **You're Done!**

The automated deployment package reduced your work from **6 hours** to **30 minutes**!

**What you did**: 3 simple steps
**What the script did**: Everything else (90% of work)

Your platform is now:
- 🌐 Live on the internet
- 🔒 Secured with HTTPS
- 📧 Sending emails
- 💾 Backing up daily
- 🛡️ Protected by firewall
- 📊 Health monitored

**Welcome to production! 🚀**
