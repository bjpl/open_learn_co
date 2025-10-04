# 🚀 OpenLearn Colombia - Quick Start Card

**Print this and keep it handy!**

---

## ⚡ 30-Second Start

### Windows
```bash
start.bat
```

### Mac/Linux
```bash
./start.sh
```

**Then open**: http://localhost:3000

---

## 🔗 Key URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main dashboard |
| **API Docs** | http://localhost:8000/docs | Interactive API |
| **Health Check** | http://localhost:8000/health | System status |

---

## 🧪 Quick Tests

### 1. Test Backend
```bash
curl http://localhost:8000/health
```
**Expected**: `{"status":"healthy"}`

### 2. Test Scraper
```bash
curl -X POST http://localhost:8000/api/v1/scraping/scrape \
  -H "Content-Type: application/json" \
  -d '{"source":"el_tiempo","count":3}'
```

### 3. View Articles
```bash
curl http://localhost:8000/api/v1/articles?limit=5
```

---

## 🛠️ Common Commands

### Start Services
```bash
# Full stack
start.bat  (Windows)
./start.sh (Mac/Linux)

# Just infrastructure
docker-compose up -d postgres redis
```

### Stop Services
```bash
# Full stack
stop.bat   (Windows)
./stop.sh  (Mac/Linux)

# Just infrastructure
docker-compose down
```

### View Logs
```bash
# Backend
tail -f logs/backend.log

# Frontend
tail -f logs/frontend.log

# Docker services
docker-compose logs -f
```

### Database Migrations
```bash
cd backend
python -m alembic upgrade head      # Apply latest
python -m alembic downgrade -1      # Rollback one
python -m alembic revision -m "msg" # Create new
```

### Scheduler
```bash
# Check status
curl http://localhost:8000/api/v1/scheduler/status

# Trigger job manually
curl -X POST http://localhost:8000/api/v1/scheduler/trigger/daily_news_scraping

# List all jobs
curl http://localhost:8000/api/v1/scheduler/jobs
```

---

## 🐛 Troubleshooting

### Problem: Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "5433:5432"  # PostgreSQL
  - "6380:6379"  # Redis
```

### Problem: Database Connection Failed
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
cd backend && python -m alembic upgrade head
```

### Problem: Module Not Found
```bash
cd backend
pip install -r requirements.txt
```

### Problem: Frontend Won't Start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Problem: Scraper Failing
```bash
# Check logs
docker-compose logs api

# Test specific scraper
curl -X POST http://localhost:8000/api/v1/scraping/test \
  -d '{"source":"el_tiempo"}'
```

---

## 📊 Health Checks

### System Status
```bash
# All services
curl http://localhost:8000/api/v1/monitoring/health

# Database
curl http://localhost:8000/api/v1/monitoring/database

# Cache
curl http://localhost:8000/api/v1/monitoring/cache
```

### Performance Metrics
```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

**Response**:
```json
{
  "response_times": {"p50": 45, "p95": 120},
  "error_rate": 0.002,
  "cache_hit_rate": 0.85,
  "scraper_success_rate": 0.92
}
```

---

## 🔐 Environment Variables

### Required (Development)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
```

### Optional (Features)
```bash
# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Error tracking
SENTRY_DSN=https://key@sentry.io/project

# Search (if using Elasticsearch)
ELASTICSEARCH_URL=http://localhost:9200
```

---

## 📝 Quick Workflows

### Daily Development
```bash
1. start.bat               # Start all services
2. Open http://localhost:3000
3. Make changes
4. Services auto-reload
5. stop.bat when done
```

### Test New Scraper
```bash
1. Create scraper file in backend/scrapers/sources/media/
2. Register in backend/scrapers/sources/__init__.py
3. Test: POST /api/v1/scraping/test
4. If works: Add to scheduled jobs
```

### Deploy to Production
```bash
1. git push origin main
2. Railway/Vercel auto-deploys
3. Run migrations: railway run alembic upgrade head
4. Verify: curl https://api.domain.com/health
```

### Add New Feature
```bash
1. Create backend endpoint (backend/app/api/)
2. Add database model if needed
3. Create migration: alembic revision
4. Build frontend component
5. Test end-to-end
6. Deploy
```

---

## 📚 Documentation Links

- **Full Launch Guide**: `/docs/LAUNCH_GUIDE.md`
- **Visual Roadmap**: `/docs/VISUAL_ROADMAP.md`
- **Deployment Checklist**: `/DEPLOYMENT_CHECKLIST.md`
- **API Documentation**: http://localhost:8000/docs
- **Architecture Guide**: `/backend/docs/architecture.md`

---

## 🚨 Emergency Contacts

### Local Issues
- Logs: `./logs/` directory
- Docker: `docker-compose logs -f`
- Database: Check `docker-compose ps postgres`

### Production Issues
- Uptime: [UptimeRobot dashboard]
- Errors: [Sentry dashboard]
- Logs: [Better Stack dashboard]
- Hosting: [Railway/DO dashboard]

---

## ✅ Pre-Launch Checklist

### Phase 1: Personal Use
- [ ] System starts successfully
- [ ] All scrapers tested
- [ ] Used daily for 1 week
- [ ] No critical bugs

### Phase 2: Production
- [ ] Deployed to hosting
- [ ] Monitoring configured
- [ ] 99% uptime for 48 hours
- [ ] SSL/HTTPS working

### Phase 3: Beta
- [ ] 5+ beta users
- [ ] Positive feedback
- [ ] Critical bugs fixed
- [ ] 60%+ retention

### Phase 4: Public
- [ ] Business model decided
- [ ] Marketing ready
- [ ] ProductHunt prepared
- [ ] Growth plan documented

---

## 🎯 Success Metrics

**Technical**:
- Uptime: 99.5%+
- Response: <200ms (p95)
- Error rate: <1%

**User**:
- Month 1: 100 users
- Month 3: 500 users
- Month 6: 2000 users

**Business**:
- Month 1: $100-500/mo
- Month 3: $500-1500/mo
- Month 6: $1500-3000/mo

---

## 💡 Pro Tips

1. **Use Scripts**: `start.bat` / `start.sh` for fastest setup
2. **Monitor Logs**: `tail -f logs/backend.log` to catch issues early
3. **Test Often**: Run test scrapers daily to ensure reliability
4. **Cache Aggressively**: Use Redis for everything possible
5. **Document Changes**: Update this card as you learn

---

## 🎉 Next Steps

1. ✅ **This Weekend**: Get it running, use it daily
2. 🚀 **Next Week**: Deploy to production
3. 👥 **Week 3-4**: Beta testing
4. 🌍 **Month 2-3**: Public launch

---

**You've got this!** 🇨🇴

Print this card and keep it at your desk for quick reference.

---

*Created: October 2025 | Version: 1.0*
