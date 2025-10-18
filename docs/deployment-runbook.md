# OpenLearn Colombia - Deployment Runbook

## Overview
This runbook provides step-by-step instructions for deploying OpenLearn Colombia to staging and production environments.

## Pre-Deployment Checklist

### 1. Code Quality
- [ ] All tests passing locally
- [ ] Code review completed and approved
- [ ] No merge conflicts
- [ ] Branch up to date with main/develop
- [ ] Version number updated (if applicable)

### 2. Environment Validation
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Static files collected
- [ ] Dependencies up to date
- [ ] Security vulnerabilities addressed

### 3. Infrastructure
- [ ] Database backup completed
- [ ] Monitoring alerts configured
- [ ] CDN cache cleared (if needed)
- [ ] DNS records verified
- [ ] SSL certificates valid

### 4. Team Communication
- [ ] Deployment scheduled and announced
- [ ] On-call engineer identified
- [ ] Stakeholders notified
- [ ] Maintenance window (if needed) communicated

## Deployment Process

### Automatic Deployment (CI/CD)

#### Staging Deployment
1. **Trigger**: Push to `develop` branch or manual workflow dispatch
2. **Automated Steps**:
   - Pre-deployment validation
   - Run tests
   - Build Docker image
   - Deploy to staging ECS
   - Run database migrations
   - Execute smoke tests
   - Run load tests

3. **Manual Verification**:
   ```bash
   # Check deployment status
   curl https://staging.openlearn.colombia/health/

   # Verify critical endpoints
   curl https://staging.openlearn.colombia/api/articles/
   curl https://staging.openlearn.colombia/api/search/?q=test
   ```

4. **Expected Timeline**: 15-20 minutes

#### Production Deployment
1. **Trigger**: Push to `main` branch or manual workflow dispatch (requires approval)
2. **Pre-Deployment**:
   - Verify staging deployment successful
   - Review load test results
   - Confirm p95 response time < 500ms
   - Get stakeholder approval

3. **Automated Steps**:
   - Create database backup
   - Build and push Docker image
   - Blue-green deployment to ECS
   - Run database migrations
   - Execute smoke tests
   - Monitor for 10 minutes

4. **Manual Verification**:
   ```bash
   # Check deployment status
   curl https://openlearn.colombia/health/

   # Verify critical functionality
   curl https://openlearn.colombia/api/articles/
   curl https://openlearn.colombia/api/dashboard/
   ```

5. **Expected Timeline**: 20-30 minutes

### Manual Deployment (Emergency)

#### Prerequisites
```bash
# Install AWS CLI
aws --version

# Configure credentials
aws configure

# Install required tools
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Staging Manual Deployment
```bash
# 1. Run pre-deployment validation
python tests/deployment/pre_deployment.py

# 2. Build Docker image
docker build -t openlearn-colombia:$(git rev-parse --short HEAD) .

# 3. Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_REGISTRY>
docker tag openlearn-colombia:$(git rev-parse --short HEAD) <ECR_REGISTRY>/openlearn-staging:latest
docker push <ECR_REGISTRY>/openlearn-staging:latest

# 4. Update ECS service
aws ecs update-service \
  --cluster openlearn-staging \
  --service openlearn-web \
  --force-new-deployment

# 5. Wait for deployment
aws ecs wait services-stable \
  --cluster openlearn-staging \
  --services openlearn-web

# 6. Run migrations
aws ecs run-task \
  --cluster openlearn-staging \
  --task-definition openlearn-migrate \
  --launch-type FARGATE

# 7. Run smoke tests
DEPLOYMENT_URL=https://staging.openlearn.colombia python tests/deployment/post_deployment.py
```

#### Production Manual Deployment
```bash
# 1. Create database backup
aws rds create-db-snapshot \
  --db-instance-identifier openlearn-production \
  --db-snapshot-identifier openlearn-pre-deploy-$(date +%Y%m%d-%H%M%S)

# 2. Wait for backup completion
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier openlearn-pre-deploy-$(date +%Y%m%d-%H%M%S)

# 3. Build and push Docker image
docker build -t openlearn-colombia:$(git rev-parse --short HEAD) .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_REGISTRY>
docker tag openlearn-colombia:$(git rev-parse --short HEAD) <ECR_REGISTRY>/openlearn-production:latest
docker push <ECR_REGISTRY>/openlearn-production:latest

# 4. Deploy to ECS with circuit breaker
aws ecs update-service \
  --cluster openlearn-production \
  --service openlearn-web \
  --force-new-deployment \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},maximumPercent=200,minimumHealthyPercent=100"

# 5. Monitor deployment
aws ecs wait services-stable \
  --cluster openlearn-production \
  --services openlearn-web \
  --timeout 600

# 6. Run migrations
aws ecs run-task \
  --cluster openlearn-production \
  --task-definition openlearn-migrate \
  --launch-type FARGATE

# 7. Verify deployment
DEPLOYMENT_URL=https://openlearn.colombia python tests/deployment/post_deployment.py
```

## Database Migrations

### Safe Migration Process
1. **Review migration files**:
   ```bash
   python manage.py showmigrations
   python manage.py sqlmigrate <app> <migration_number>
   ```

2. **Test migrations on staging**:
   ```bash
   # Backup staging database first
   python manage.py migrate --plan
   python manage.py migrate
   ```

3. **Run on production**:
   ```bash
   # During maintenance window if needed
   python manage.py migrate --no-input
   ```

### Rollback Migrations
```bash
# Rollback last migration
python manage.py migrate <app> <previous_migration>

# Or rollback all migrations for an app
python manage.py migrate <app> zero
```

## Rollback Procedures

### Immediate Rollback (< 30 minutes)

#### Option 1: ECS Task Definition Rollback
```bash
# 1. Get previous task definition
aws ecs describe-services \
  --cluster openlearn-production \
  --services openlearn-web \
  --query 'services[0].deployments[1].taskDefinition'

# 2. Update service to previous task definition
aws ecs update-service \
  --cluster openlearn-production \
  --service openlearn-web \
  --task-definition <previous-task-definition>

# 3. Wait for rollback
aws ecs wait services-stable \
  --cluster openlearn-production \
  --services openlearn-web
```

#### Option 2: Docker Image Rollback
```bash
# 1. Find previous image tag
aws ecr describe-images \
  --repository-name openlearn-production \
  --query 'sort_by(imageDetails, &imagePushedAt)[-2].imageTags[0]'

# 2. Update ECS service with previous image
# (Update task definition with previous image tag, then update service)
```

### Database Rollback
```bash
# 1. Stop application traffic
aws ecs update-service \
  --cluster openlearn-production \
  --service openlearn-web \
  --desired-count 0

# 2. Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier openlearn-production-restored \
  --db-snapshot-identifier <snapshot-id>

# 3. Wait for restore
aws rds wait db-instance-available \
  --db-instance-identifier openlearn-production-restored

# 4. Update DNS or connection string
# 5. Resume application traffic
```

### Complete Environment Rollback
```bash
# Use Infrastructure as Code (Terraform/CloudFormation)
# to restore entire environment to previous state

# Terraform example:
terraform plan -target=module.production
terraform apply -auto-approve
```

## Post-Deployment Monitoring

### Immediate (0-30 minutes)
```bash
# 1. Monitor application logs
aws logs tail /ecs/openlearn-production --follow

# 2. Check error rates
# CloudWatch dashboard: openlearn-production-metrics

# 3. Monitor response times
# Target: p95 < 500ms

# 4. Check database connections
# RDS Performance Insights dashboard
```

### Short-term (30 minutes - 4 hours)
- Monitor user complaints/support tickets
- Check application metrics trends
- Review error logs for new issues
- Verify scheduled tasks running
- Monitor database performance

### Long-term (4+ hours)
- Analyze performance trends
- Review cost implications
- Check backup completion
- Monitor resource utilization
- Review security logs

## Troubleshooting

### Deployment Fails
1. **Check ECS service events**:
   ```bash
   aws ecs describe-services \
     --cluster openlearn-production \
     --services openlearn-web \
     --query 'services[0].events[0:10]'
   ```

2. **Check task logs**:
   ```bash
   aws logs tail /ecs/openlearn-production --follow
   ```

3. **Verify environment variables**:
   ```bash
   aws ecs describe-task-definition \
     --task-definition openlearn-web \
     --query 'taskDefinition.containerDefinitions[0].environment'
   ```

### High Error Rate After Deployment
1. **Check application logs** for error patterns
2. **Review recent code changes** for bugs
3. **Check database connectivity** and query performance
4. **Verify third-party service availability**
5. **Consider rollback** if error rate > 5%

### Performance Degradation
1. **Check database queries** for N+1 problems
2. **Review cache hit rate** in Redis
3. **Check CDN cache** effectiveness
4. **Monitor database connection pool**
5. **Review application profiling** data

### Database Migration Fails
1. **Check migration logs** for specific error
2. **Verify database permissions**
3. **Check for locking issues**
4. **Review migration SQL** for syntax errors
5. **Rollback migration** and fix issues

## Emergency Contacts

- **On-Call Engineer**: [Phone/Slack]
- **DevOps Lead**: [Phone/Slack]
- **Database Admin**: [Phone/Slack]
- **Product Manager**: [Phone/Slack]
- **AWS Support**: [Account details]

## Runbook Maintenance

This runbook should be updated:
- After each deployment
- When infrastructure changes
- When new tools are introduced
- Quarterly review at minimum

**Last Updated**: 2025-10-17
**Version**: 1.0
**Owner**: DevOps Team
