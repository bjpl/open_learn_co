# Quick Start: Deploying OpenLearn Colombia

## 🎯 Goal
Deploy OpenLearn Colombia to production with confidence using automated validation and load testing.

## ⚡ 5-Minute Quick Start

### 1. Pre-Flight Check (30 seconds)
```bash
# Ensure you're in the project root
cd /path/to/open_learn

# Verify you have required tools
python3 --version  # Should be 3.11+
docker --version   # Required for builds
aws --version      # Required for deployments
```

### 2. Install Test Dependencies (1 minute)
```bash
pip install -r requirements-test.txt
```

### 3. Run Pre-Deployment Validation (2 minutes)
```bash
# Set environment variables (example)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/openlearn"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key-here"
export DEBUG="False"
export ALLOWED_HOSTS="localhost,openlearn.colombia"

# Run validation
./scripts/deployment/validate-deployment.sh pre local
```

**Expected Output**:
```
✅ PRE-DEPLOYMENT VALIDATION PASSED
```

### 4. Run Load Tests (2 minutes)
```bash
# Start your Django server in another terminal
python manage.py runserver

# Run load tests
./scripts/deployment/run-load-tests.sh local 100 2m
```

**Expected Output**:
```
✅ p95 response time meets target (<500ms)
✅ LOAD TEST PASSED
```

---

## 📋 Complete Deployment Flow

### Option A: Automated CI/CD (Recommended)

#### Step 1: Prepare Your Code
```bash
# Ensure all tests pass locally
pytest tests/

# Commit your changes
git add .
git commit -m "feat: add new feature"
```

#### Step 2: Deploy to Staging
```bash
# Push to develop branch
git checkout develop
git merge your-feature-branch
git push origin develop
```

**What Happens Automatically**:
1. ✅ Pre-deployment validation runs
2. ✅ Unit tests execute
3. ✅ Docker image builds
4. ✅ Deploys to staging ECS
5. ✅ Post-deployment smoke tests run
6. ✅ Load tests execute (1000 users)
7. ✅ GitHub Actions reports results

**Monitor Progress**:
- GitHub Actions: `https://github.com/your-org/open_learn/actions`
- Expected duration: 15-20 minutes

#### Step 3: Deploy to Production
```bash
# Merge to main branch
git checkout main
git merge develop
git push origin main
```

**What Happens**:
1. ⏸️  Workflow waits for manual approval
2. 👤 Approve deployment in GitHub Actions
3. ✅ Database backup created automatically
4. ✅ Blue-green deployment to production ECS
5. ✅ Smoke tests validate deployment
6. 📧 Team notified via Slack

**Monitor Production**:
- Application: `https://openlearn.colombia/health/`
- Metrics: CloudWatch Dashboard
- Logs: AWS CloudWatch Logs

---

### Option B: Manual Deployment (Emergency/Advanced)

#### Pre-Deployment Validation
```bash
# 1. Validate environment
./scripts/deployment/validate-deployment.sh pre staging

# 2. If validation passes, proceed
# If it fails, fix issues before deploying
```

#### Build and Push Docker Image
```bash
# 1. Build image
docker build -t openlearn-colombia:$(git rev-parse --short HEAD) .

# 2. Test image locally
docker run --rm openlearn-colombia:$(git rev-parse --short HEAD) python manage.py check

# 3. Tag for ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <YOUR_ECR_REGISTRY>

docker tag openlearn-colombia:$(git rev-parse --short HEAD) \
  <YOUR_ECR_REGISTRY>/openlearn-staging:latest

# 4. Push to ECR
docker push <YOUR_ECR_REGISTRY>/openlearn-staging:latest
```

#### Deploy to ECS
```bash
# 1. Update ECS service
aws ecs update-service \
  --cluster openlearn-staging \
  --service openlearn-web \
  --force-new-deployment

# 2. Wait for deployment
aws ecs wait services-stable \
  --cluster openlearn-staging \
  --services openlearn-web

# 3. Run database migrations
aws ecs run-task \
  --cluster openlearn-staging \
  --task-definition openlearn-migrate \
  --launch-type FARGATE
```

#### Post-Deployment Validation
```bash
# 1. Run smoke tests
DEPLOYMENT_URL=https://staging.openlearn.colombia \
  ./scripts/deployment/validate-deployment.sh post staging

# 2. Run load tests
./scripts/deployment/run-load-tests.sh staging 1000 5m

# 3. Monitor for 30 minutes
# Check CloudWatch metrics, logs, and error rates
```

---

## 🚨 Emergency Rollback

If deployment fails or critical issues detected:

### Quick Rollback (< 5 minutes)
```bash
# Rollback application to previous version
./scripts/deployment/rollback.sh production application
```

### Full Rollback with Database (15 minutes)
```bash
# Rollback application AND database
./scripts/deployment/rollback.sh production full
```

**Safety Features**:
- Production requires typing "rollback production"
- Automatic verification after rollback
- Team notification via Slack/email

---

## 📊 Performance Validation

### Load Test Results Interpretation

#### ✅ PASSED Example:
```
Performance Summary:
  Average Response Time: 142ms
  p95 Response Time: 387ms  ← Under 500ms target ✓
  p99 Response Time: 654ms
  Failure Rate: 0.12%       ← Under 1% target ✓
  Requests/sec: 234         ← Above 100 req/s target ✓

✅ LOAD TEST PASSED
```

#### ❌ FAILED Example:
```
Performance Summary:
  Average Response Time: 342ms
  p95 Response Time: 876ms  ← Exceeds 500ms target ✗
  p99 Response Time: 2341ms
  Failure Rate: 3.45%       ← Exceeds 1% target ✗
  Requests/sec: 87          ← Below 100 req/s target ✗

❌ LOAD TEST FAILED
```

**Action for Failed Tests**:
1. Review application logs for errors
2. Check database query performance
3. Verify Redis cache hit rate
4. Scale infrastructure if needed
5. Do NOT deploy to production until passing

---

## 🔍 Monitoring Post-Deployment

### First 30 Minutes (Critical)
```bash
# Monitor application logs
aws logs tail /ecs/openlearn-production --follow

# Check error rate
# Target: < 1% error rate

# Monitor response times
# Target: p95 < 500ms
```

### First 4 Hours (Important)
- ✅ Monitor CloudWatch dashboards
- ✅ Check user feedback/support tickets
- ✅ Review database performance
- ✅ Verify scheduled tasks running
- ✅ Check resource utilization

### First 24 Hours (Continuous)
- ✅ Compare metrics to baseline
- ✅ Monitor costs
- ✅ Verify backups completed
- ✅ Review security logs

---

## 🛠️ Troubleshooting Common Issues

### Issue: Pre-Deployment Validation Fails

**Symptom**:
```
❌ Required environment variable missing: DATABASE_URL
❌ PRE-DEPLOYMENT VALIDATION FAILED
```

**Solution**:
```bash
# Set missing environment variables
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."
# ... etc

# Re-run validation
./scripts/deployment/validate-deployment.sh pre local
```

---

### Issue: Load Tests Show High Response Times

**Symptom**:
```
p95 Response Time: 1234ms ← Exceeds 500ms target
```

**Solutions**:
1. **Check database queries**:
   ```bash
   # Review slow queries
   python manage.py debugsqlshell
   ```

2. **Check cache hit rate**:
   ```bash
   redis-cli INFO stats
   # Look for keyspace_hits vs keyspace_misses
   ```

3. **Profile application**:
   ```bash
   pip install django-silk
   # Add silk to INSTALLED_APPS
   # Review /silk/ dashboard
   ```

4. **Scale infrastructure**:
   ```bash
   # Increase ECS task count
   aws ecs update-service \
     --cluster openlearn-production \
     --service openlearn-web \
     --desired-count 4
   ```

---

### Issue: Deployment Successful but Smoke Tests Fail

**Symptom**:
```
❌ Health endpoint: 500
❌ POST-DEPLOYMENT SMOKE TESTS FAILED
```

**Solutions**:
1. **Check application logs**:
   ```bash
   aws logs tail /ecs/openlearn-production --follow
   ```

2. **Verify environment variables**:
   ```bash
   aws ecs describe-task-definition \
     --task-definition openlearn-web \
     --query 'taskDefinition.containerDefinitions[0].environment'
   ```

3. **Check database connectivity**:
   ```bash
   # SSH into ECS task
   aws ecs execute-command \
     --cluster openlearn-production \
     --task <task-id> \
     --container web \
     --command "/bin/bash" \
     --interactive

   # Test database connection
   python manage.py dbshell
   ```

4. **Consider rollback**:
   ```bash
   ./scripts/deployment/rollback.sh production application
   ```

---

## 📚 Reference Documentation

### Quick Links
- **Deployment Runbook**: `/docs/deployment-runbook.md`
- **Load Testing Guide**: `/tests/load/README.md`
- **Validation Summary**: `/docs/DEPLOYMENT_VALIDATION_SUMMARY.md`
- **CI/CD Pipeline**: `.github/workflows/deploy.yml`

### Scripts Reference
```bash
# Pre-deployment validation
./scripts/deployment/validate-deployment.sh pre [local|staging|production]

# Post-deployment validation
./scripts/deployment/validate-deployment.sh post [staging|production]

# Load testing
./scripts/deployment/run-load-tests.sh [staging|production] [users] [duration]

# Emergency rollback
./scripts/deployment/rollback.sh [staging|production] [application|database|full]
```

### Python Scripts
```bash
# Pre-deployment validation (direct)
python tests/deployment/pre_deployment.py

# Post-deployment smoke tests (direct)
DEPLOYMENT_URL=https://staging.openlearn.colombia \
  python tests/deployment/post_deployment.py

# Load testing (direct)
locust -f tests/load/locustfile.py \
  --host https://staging.openlearn.colombia \
  --users 1000 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] All tests passing locally
- [ ] Code review completed
- [ ] Pre-deployment validation passed
- [ ] Database migrations reviewed
- [ ] Environment variables configured
- [ ] Team notified of deployment schedule

### During Deployment
- [ ] Monitor CI/CD pipeline progress
- [ ] Review build logs for errors
- [ ] Verify staging deployment successful
- [ ] Check smoke test results
- [ ] Review load test performance
- [ ] Approve production deployment (if required)

### After Deployment
- [ ] Smoke tests passed
- [ ] Response times within targets
- [ ] Error rate < 1%
- [ ] Database migrations applied
- [ ] Static files accessible
- [ ] Monitor for 30 minutes minimum
- [ ] Team notified of completion

### If Issues Detected
- [ ] Assess severity (critical vs non-critical)
- [ ] Review logs and metrics
- [ ] Attempt fix if minor
- [ ] Execute rollback if critical
- [ ] Document incident
- [ ] Post-mortem if needed

---

## 🎓 Training Resources

### For First-Time Deployers
1. Read deployment runbook: `/docs/deployment-runbook.md`
2. Practice in staging environment
3. Run load tests locally
4. Execute test rollback in staging
5. Shadow experienced deployer

### For Ongoing Learning
- Review deployment metrics weekly
- Practice rollback procedures monthly
- Update documentation based on lessons learned
- Stay current with AWS best practices

---

## 🆘 Getting Help

### Self-Service
1. Check deployment runbook
2. Review load testing guide
3. Search application logs
4. Check CloudWatch metrics

### Escalation
1. Post in #devops Slack channel
2. Contact on-call engineer
3. Create incident ticket
4. Emergency: Call DevOps lead

---

## 📞 Emergency Contacts

**During Business Hours**:
- DevOps Team: #devops Slack channel
- Database Admin: [Contact info]

**After Hours**:
- On-Call Engineer: [Pager/Phone]
- Backup On-Call: [Pager/Phone]

**AWS Support**:
- Account: [AWS Account ID]
- Support Plan: Business/Enterprise
- Phone: 1-866-CALL-AWS

---

## 🚀 You're Ready!

This deployment validation suite provides enterprise-grade confidence in your deployments:

- ✅ Automated validation before deployment
- ✅ Load testing with 1000+ concurrent users
- ✅ CI/CD pipeline with quality gates
- ✅ One-command emergency rollback
- ✅ Comprehensive monitoring and alerting

**Start your first deployment**:
```bash
git checkout develop
git merge your-feature
git push origin develop
```

Watch GitHub Actions do the rest!

---

**Last Updated**: 2025-10-17
**Version**: 1.0
**Maintained By**: DevOps Team
