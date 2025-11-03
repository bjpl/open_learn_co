# Production Deployment Security Checklist
## OpenLearn Colombia Platform

**IMPORTANT**: Complete ALL items in this checklist before deploying to production or making the repository public.

---

## 🔴 CRITICAL - Must Complete Before Public Release

### Secrets & Credentials

- [ ] **Generate new SECRET_KEY**
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  - [ ] Update `.env` with new key
  - [ ] Verify old key is NOT in codebase

- [ ] **Rotate ALL compromised credentials**
  - [ ] New Redis credentials (old: `REDACTED_REDIS_PASSWORD`)
  - [ ] New PostgreSQL password (old: `colombian_pass`)
  - [ ] New database user if needed
  - [ ] Revoke/regenerate all API keys

- [ ] **Clean Git History**
  - [ ] Install git-filter-repo: `pip install git-filter-repo`
  - [ ] Remove .env from history:
    ```bash
    git filter-repo --path .env --invert-paths
    ```
  - [ ] Remove hardcoded secrets:
    ```bash
    git filter-repo --replace-text secrets.txt
    ```
    (Create secrets.txt with: `57eb2b13...==>REDACTED_SECRET_KEY`)
  - [ ] Force push cleaned history
  - [ ] Verify secrets removed: `git log --all -p | grep "lXXQHqXVy"`

- [ ] **Verify .env is gitignored**
  ```bash
  git check-ignore .env  # Should output: .env
  git ls-files .env      # Should output nothing
  ```

### Environment Configuration

- [ ] **Copy .env.example to .env**
  ```bash
  cp .env.example .env
  ```

- [ ] **Update all placeholder values in .env**
  - [ ] `SECRET_KEY` - New random value
  - [ ] `DATABASE_URL` - Production database connection
  - [ ] `REDIS_URL` - Production Redis connection
  - [ ] `CELERY_BROKER_URL` - Production Celery broker
  - [ ] `CELERY_RESULT_BACKEND` - Production result backend
  - [ ] `CORS_ALLOWED_ORIGINS` - Production domain(s) ONLY
  - [ ] API keys for Colombian government services
  - [ ] Email credentials (if using email features)
  - [ ] Sentry DSN (if using error tracking)

- [ ] **Set production security flags**
  - [ ] `ENVIRONMENT=production`
  - [ ] `DEBUG=false`
  - [ ] `SESSION_COOKIE_SECURE=true`
  - [ ] Remove wildcard from CORS: `CORS_ALLOWED_ORIGINS=https://yourdomain.com`

---

## 🟠 HIGH PRIORITY - Complete Before Launch

### Dependency Security

- [ ] **Update frontend dependencies**
  ```bash
  cd frontend
  npm audit fix
  npm update
  npm audit  # Verify no critical vulnerabilities
  ```

- [ ] **Update backend dependencies**
  ```bash
  cd backend
  pip list --outdated
  pip install -U safety bandit
  safety check
  bandit -r . -ll
  ```

- [ ] **Review and address all security warnings**
  - Document any accepted risks
  - Create issues for deferred updates

### GitHub Security Setup

- [ ] **Enable GitHub security features**
  - [ ] Go to Settings → Security & analysis
  - [ ] Enable Dependabot alerts
  - [ ] Enable Dependabot security updates
  - [ ] Enable Code scanning (CodeQL)
  - [ ] Enable Secret scanning

- [ ] **Configure Dependabot**
  - [ ] Verify `.github/dependabot.yml` exists
  - [ ] Update reviewer usernames
  - [ ] Test by checking for Dependabot PRs

- [ ] **Set up security workflows**
  - [ ] Verify `.github/workflows/security-scan.yml` exists
  - [ ] Run workflow manually to test
  - [ ] Review and address any findings

### Authentication & Authorization

- [ ] **Verify JWT configuration**
  - [ ] Access token expiration appropriate (default 30min)
  - [ ] Refresh token expiration appropriate (default 7 days)
  - [ ] Token signature using strong SECRET_KEY

- [ ] **Test authentication flow**
  - [ ] Registration works
  - [ ] Login works
  - [ ] Token refresh works
  - [ ] Logout clears tokens
  - [ ] Protected routes require authentication

- [ ] **Password security**
  - [ ] Minimum length enforced (8+ chars)
  - [ ] Complexity requirements enforced
  - [ ] Bcrypt hashing configured
  - [ ] No plain text passwords logged

### API Security

- [ ] **CORS configuration**
  - [ ] No wildcards (`*`) in production
  - [ ] Specific domains only
  - [ ] `allow_credentials=true` if needed
  - [ ] Test cross-origin requests

- [ ] **Rate limiting**
  - [ ] Rate limiting middleware enabled
  - [ ] Appropriate limits set:
    - API: 60-100 requests/minute
    - Auth: 5 attempts/minute
    - File uploads: 10/minute
  - [ ] Test rate limiting works

- [ ] **Input validation**
  - [ ] All endpoints use Pydantic schemas
  - [ ] File uploads validated (type, size)
  - [ ] SQL injection protection via ORM
  - [ ] No raw SQL with user input

---

## 🟡 MEDIUM PRIORITY - Complete Within First Week

### Infrastructure Security

- [ ] **HTTPS/TLS Configuration**
  - [ ] SSL certificate installed (Let's Encrypt recommended)
  - [ ] HTTP redirects to HTTPS
  - [ ] HSTS header enabled
  - [ ] Test with SSL Labs: https://www.ssllabs.com/ssltest/

- [ ] **Firewall Configuration**
  - [ ] Only ports 80, 443 open to public
  - [ ] Database port (5432) restricted to backend only
  - [ ] Redis port (6379) restricted to backend only
  - [ ] SSH (22) restricted to admin IPs only

- [ ] **Database Security**
  - [ ] Strong password set
  - [ ] Not exposed to public internet
  - [ ] Connection encryption enabled
  - [ ] Backup encryption enabled
  - [ ] Regular backups scheduled

- [ ] **Logging & Monitoring**
  - [ ] Centralized logging configured
  - [ ] Error tracking setup (Sentry)
  - [ ] Uptime monitoring configured
  - [ ] Security alerts configured
  - [ ] Log rotation enabled

### Application Security

- [ ] **Security headers**
  - [ ] Add SecurityHeadersMiddleware to app
  - [ ] Test headers with: https://securityheaders.com/
  - [ ] CSP policy appropriate for app
  - [ ] X-Frame-Options prevents clickjacking

- [ ] **File Upload Security** (if applicable)
  - [ ] File type validation
  - [ ] File size limits
  - [ ] Virus scanning
  - [ ] Stored outside webroot
  - [ ] Random filenames

- [ ] **Error Handling**
  - [ ] No stack traces in production
  - [ ] Generic error messages to users
  - [ ] Detailed errors logged securely
  - [ ] No sensitive data in error messages

---

## 🟢 LOW PRIORITY - Complete Within First Month

### Documentation

- [ ] **Security documentation**
  - [ ] README.md updated with security notes
  - [ ] SECURITY.md published (exists in `.github/`)
  - [ ] Deployment guide includes security steps
  - [ ] Security contact information published

- [ ] **Team Training**
  - [ ] Team knows how to report vulnerabilities
  - [ ] Incident response plan documented
  - [ ] Key rotation procedures documented
  - [ ] Backup restoration tested

### Compliance & Best Practices

- [ ] **Privacy Compliance**
  - [ ] Privacy policy published
  - [ ] Data collection documented
  - [ ] User data export available
  - [ ] Data deletion implemented
  - [ ] Cookie consent if needed (GDPR/CCPA)

- [ ] **Security Testing**
  - [ ] Basic penetration testing completed
  - [ ] OWASP Top 10 vulnerabilities checked
  - [ ] Dependency scanning automated
  - [ ] Security scan in CI/CD pipeline

- [ ] **Regular Maintenance**
  - [ ] Weekly log review scheduled
  - [ ] Monthly dependency updates scheduled
  - [ ] Quarterly security audits scheduled
  - [ ] Backup restoration tested quarterly

---

## 📋 Quick Verification Commands

Run these commands to verify security configuration:

```bash
# Check .env is not in git
git ls-files .env  # Should be empty

# Check for secrets in git history
git log --all -p | grep -i "password\|secret\|key" | wc -l  # Should be 0 or minimal

# Check frontend vulnerabilities
cd frontend && npm audit --json | jq '.metadata.vulnerabilities'

# Check backend for security issues
cd backend && bandit -r . -ll

# Verify environment variables are set
python3 -c "import os; print('SECRET_KEY set:', bool(os.getenv('SECRET_KEY')))"

# Test HTTPS redirect
curl -I http://yourdomain.com  # Should redirect to https://

# Test security headers
curl -I https://yourdomain.com | grep -i "strict-transport\|x-frame\|x-content"
```

---

## 🚨 Emergency Procedures

### If Secrets Are Compromised

1. **Immediately rotate all credentials**
   - Generate new SECRET_KEY
   - Change all database passwords
   - Revoke all API keys
   - Regenerate Redis credentials

2. **Invalidate all user sessions**
   ```python
   # In backend, invalidate all JWTs by changing SECRET_KEY
   # Or add token blacklist system
   ```

3. **Notify affected parties**
   - Users (if user data exposed)
   - Team members
   - Infrastructure providers

4. **Document incident**
   - What was compromised
   - When it was discovered
   - Actions taken
   - Lessons learned

### Security Contact

- **Primary**: [your-security-email@domain.com]
- **Backup**: [your-backup-contact@domain.com]
- **Emergency**: [your-phone-number]

---

## ✅ Final Pre-Launch Checklist

Right before making repository public or deploying to production:

- [ ] All CRITICAL items completed
- [ ] All HIGH PRIORITY items completed
- [ ] Git history cleaned and verified
- [ ] All secrets rotated
- [ ] Production .env configured
- [ ] HTTPS enabled and working
- [ ] Backups configured and tested
- [ ] Monitoring and alerts configured
- [ ] Security documentation published
- [ ] Team briefed on security procedures

---

**Sign-off**:

- [ ] Security review completed by: __________________ Date: __________
- [ ] Deployment approved by: __________________ Date: __________

---

**Remember**: Security is an ongoing process. Schedule regular reviews of this checklist and update it as threats evolve.
