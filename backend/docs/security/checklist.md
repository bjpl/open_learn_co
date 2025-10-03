# Security Checklist - OpenLearn Colombia Platform

## Pre-Deployment Security Checklist

This checklist must be completed and verified before deploying to production. Each item represents a critical security control that protects the platform and user data.

---

## CRITICAL - Must Complete Before Production

### 1. Secrets and Credentials Management

- [ ] **SECRET_KEY Configuration**
  ```bash
  # Generate secure SECRET_KEY
  python backend/scripts/generate_secret_key.py

  # Verify length >= 64 characters
  # Verify high entropy (not dictionary words)
  # Verify NOT committed to git
  ```
  - [ ] SECRET_KEY set via environment variable
  - [ ] SECRET_KEY is >= 64 characters
  - [ ] SECRET_KEY is cryptographically random
  - [ ] DEFAULT_KEY removed from settings.py
  - [ ] Verified SECRET_KEY not in git history

- [ ] **Database Credentials**
  - [ ] POSTGRES_PASSWORD set via environment variable
  - [ ] Password is strong (16+ characters, mixed case, symbols)
  - [ ] Default password removed from settings.py
  - [ ] Database user has minimum required privileges
  - [ ] Connection string not logged anywhere

- [ ] **API Keys and Tokens**
  - [ ] All API keys stored in environment variables
  - [ ] No API keys in configuration files
  - [ ] No API keys in source code
  - [ ] API keys rotated if previously exposed
  - [ ] API key access logged and monitored

### 2. Security Headers

- [ ] **Security Headers Middleware Applied**
  ```python
  # In app/main.py
  from app.middleware.security_headers import add_security_middleware
  add_security_middleware(app, settings)
  ```
  - [ ] HSTS header configured (max-age >= 31536000)
  - [ ] CSP header configured (no 'unsafe-inline' scripts)
  - [ ] X-Frame-Options set to DENY
  - [ ] X-Content-Type-Options set to nosniff
  - [ ] Referrer-Policy configured
  - [ ] Permissions-Policy configured

- [ ] **Verify Headers**
  ```bash
  # Test security headers
  curl -I https://your-domain.com | grep -i "strict-transport\|content-security\|x-frame"
  ```

### 3. CORS Configuration

- [ ] **Strict CORS Policy**
  ```python
  # Verify in app/main.py
  allow_origins=["https://yourdomain.com"]  # NO wildcards!
  allow_credentials=True
  allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
  allow_headers=["Content-Type", "Authorization", "Accept"]
  ```
  - [ ] No wildcard (*) in allowed_origins
  - [ ] Only production domains in allowed_origins
  - [ ] Specific methods listed (not ["*"])
  - [ ] Specific headers listed (not ["*"])
  - [ ] Testing domains removed for production

### 4. HTTPS and SSL/TLS

- [ ] **HTTPS Enforcement**
  - [ ] SSL certificate installed and valid
  - [ ] HTTP redirects to HTTPS
  - [ ] HSTS header configured
  - [ ] No mixed content warnings
  - [ ] TLS 1.2 or higher only
  - [ ] Strong cipher suites configured

- [ ] **SSL Configuration**
  ```nginx
  # Example nginx configuration
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';
  ssl_prefer_server_ciphers off;
  ```

### 5. Authentication and Authorization

- [ ] **Password Security**
  - [ ] Password minimum length: 12 characters
  - [ ] Password complexity requirements enforced
  - [ ] Passwords hashed with bcrypt (cost factor >= 12)
  - [ ] No password hints or recovery questions
  - [ ] Password reset tokens expire in 1 hour

- [ ] **Session Management**
  - [ ] JWT tokens signed with strong secret
  - [ ] Access tokens expire in 15-30 minutes
  - [ ] Refresh tokens properly validated
  - [ ] Token revocation mechanism implemented
  - [ ] Session fixation protection enabled

- [ ] **Authentication Endpoints**
  - [ ] Rate limiting on /auth/login (5 attempts/minute)
  - [ ] Rate limiting on /auth/register (3 attempts/hour)
  - [ ] Rate limiting on /auth/password-reset (3 attempts/hour)
  - [ ] Failed login attempts logged
  - [ ] Account lockout after 5 failed attempts

### 6. Input Validation and Sanitization

- [ ] **Input Validation**
  - [ ] All user inputs validated with Pydantic models
  - [ ] String length limits enforced
  - [ ] Email validation using EmailStr
  - [ ] URL validation for external links
  - [ ] File upload validation (type, size, content)

- [ ] **Output Encoding**
  - [ ] HTML content sanitized (use bleach)
  - [ ] SQL queries parameterized (no string concatenation)
  - [ ] JSON responses properly escaped
  - [ ] Error messages don't reveal sensitive data

### 7. Rate Limiting

- [ ] **API Rate Limits Configured**
  ```python
  # Different limits per endpoint type
  /api/auth/* - 5 requests/minute per IP
  /api/scraping/* - 10 requests/minute per user
  /api/analysis/* - 60 requests/minute per user
  ```
  - [ ] Rate limiting middleware installed
  - [ ] Redis configured for rate limit storage
  - [ ] Different limits for anonymous vs authenticated
  - [ ] Rate limit headers returned (X-RateLimit-*)
  - [ ] 429 responses properly handled

### 8. Dependency Security

- [ ] **Vulnerability Scanning**
  ```bash
  # Scan dependencies
  pip install safety
  safety check --json

  # Update vulnerable packages
  pip install --upgrade aiohttp sqlalchemy fastapi
  ```
  - [ ] All dependencies updated to latest secure versions
  - [ ] No high/critical CVEs in dependencies
  - [ ] Automated dependency scanning in CI/CD
  - [ ] Dependency update policy established

### 9. Error Handling and Logging

- [ ] **Production Error Handling**
  - [ ] Debug mode disabled (DEBUG=False)
  - [ ] Stack traces not exposed to users
  - [ ] Generic error messages for production
  - [ ] Detailed errors logged server-side only
  - [ ] 500 errors trigger alerts

- [ ] **Security Event Logging**
  - [ ] Failed authentication attempts logged
  - [ ] Authorization failures logged
  - [ ] Suspicious activity logged
  - [ ] Admin actions logged
  - [ ] Logs sent to centralized logging (Sentry, etc.)

### 10. Database Security

- [ ] **Database Configuration**
  - [ ] Database not accessible from public internet
  - [ ] Firewall rules restrict database access
  - [ ] Database user has minimum privileges
  - [ ] Sensitive data encrypted at rest
  - [ ] Database backups encrypted

- [ ] **Query Security**
  - [ ] All queries use parameterized statements
  - [ ] No dynamic SQL with user input
  - [ ] ORM (SQLAlchemy) used for queries
  - [ ] Database error messages sanitized

---

## HIGH PRIORITY - Complete Before Launch

### 11. CSRF Protection

- [ ] **CSRF Tokens**
  ```bash
  pip install fastapi-csrf-protect
  ```
  - [ ] CSRF protection enabled for state-changing operations
  - [ ] CSRF tokens validated on POST/PUT/DELETE
  - [ ] SameSite cookie attribute set
  - [ ] Double-submit cookie pattern implemented

### 12. Security Monitoring

- [ ] **Monitoring Tools Configured**
  - [ ] Sentry for error tracking
  - [ ] Prometheus for metrics
  - [ ] Structured logging (JSON format)
  - [ ] Security event alerting
  - [ ] Automated log analysis

- [ ] **Alerts Configured**
  - [ ] Failed login spike alerts
  - [ ] High error rate alerts
  - [ ] Unusual API usage alerts
  - [ ] Database connection alerts
  - [ ] SSL certificate expiration alerts

### 13. File Upload Security

- [ ] **Upload Validation**
  - [ ] File type validation (whitelist only)
  - [ ] File size limits enforced
  - [ ] File content validation (magic bytes)
  - [ ] Uploaded files scanned for malware
  - [ ] Files stored outside webroot

### 14. API Security

- [ ] **API Endpoints**
  - [ ] All sensitive endpoints require authentication
  - [ ] Authorization checks on all resources
  - [ ] API versioning implemented
  - [ ] Deprecated endpoints documented
  - [ ] API documentation access controlled

### 15. Third-Party Integrations

- [ ] **External Services**
  - [ ] API keys for external services secured
  - [ ] Webhook signatures validated
  - [ ] External API calls have timeouts
  - [ ] SSL/TLS verification enabled
  - [ ] Third-party code audited

---

## MEDIUM PRIORITY - First Sprint

### 16. Content Security

- [ ] **XSS Prevention**
  - [ ] User-generated content sanitized
  - [ ] Markdown rendering configured securely
  - [ ] Rich text editor sanitizes output
  - [ ] CSP prevents inline scripts

### 17. Infrastructure Security

- [ ] **Server Hardening**
  - [ ] OS security updates automated
  - [ ] Unnecessary services disabled
  - [ ] Firewall configured (UFW/iptables)
  - [ ] SSH key-based auth only
  - [ ] Root login disabled

### 18. Backup and Recovery

- [ ] **Data Protection**
  - [ ] Automated backups configured
  - [ ] Backup encryption enabled
  - [ ] Backup restoration tested
  - [ ] Backup retention policy defined
  - [ ] Disaster recovery plan documented

### 19. Compliance

- [ ] **Privacy and Compliance**
  - [ ] Privacy policy published
  - [ ] Terms of service published
  - [ ] Cookie consent implemented
  - [ ] Data retention policy defined
  - [ ] GDPR compliance (if applicable)

### 20. Security Documentation

- [ ] **Documentation Complete**
  - [ ] Security.txt file published
  - [ ] Incident response plan documented
  - [ ] Security contact information public
  - [ ] Vulnerability disclosure policy published
  - [ ] Security training for team completed

---

## ONGOING - Post-Deployment

### 21. Penetration Testing

- [ ] **Security Testing**
  - [ ] OWASP ZAP scan completed
  - [ ] Manual penetration testing completed
  - [ ] Findings remediated
  - [ ] Retest after fixes
  - [ ] Quarterly security assessments scheduled

### 22. Security Updates

- [ ] **Maintenance**
  - [ ] Dependency updates weekly
  - [ ] Security patches applied within 48 hours
  - [ ] Security advisories monitored
  - [ ] Changelog maintained
  - [ ] Rollback plan tested

### 23. Access Control

- [ ] **User Management**
  - [ ] Admin accounts use MFA
  - [ ] Service accounts documented
  - [ ] Access reviews quarterly
  - [ ] Privileged access logged
  - [ ] Offboarding process enforced

### 24. Incident Response

- [ ] **Response Plan**
  - [ ] Incident response team identified
  - [ ] Communication plan defined
  - [ ] Forensics tools available
  - [ ] Incident log template created
  - [ ] Post-mortem process defined

### 25. Security Culture

- [ ] **Team Security**
  - [ ] Security training for all developers
  - [ ] Code review includes security checks
  - [ ] Security champions identified
  - [ ] Security metrics tracked
  - [ ] Bug bounty program considered

---

## Verification Commands

### Security Headers Test
```bash
# Test all security headers
curl -I https://your-domain.com/

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# Content-Security-Policy: default-src 'self'; ...
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
```

### Dependency Vulnerability Scan
```bash
# Install and run safety
pip install safety
safety check --json

# Install and run bandit
pip install bandit
bandit -r app/ -f json -o security/bandit-report.json
```

### SSL/TLS Configuration Test
```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443 -tls1_2

# Test with SSL Labs
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### Rate Limiting Test
```bash
# Test rate limits
for i in {1..10}; do
  curl -X POST https://your-domain.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test"}'
done

# Expected: 429 Too Many Requests after limit exceeded
```

### Authentication Security Test
```bash
# Test token expiration
# 1. Login and get token
TOKEN=$(curl -X POST https://your-domain.com/api/auth/login ... | jq -r .access_token)

# 2. Wait for expiration time
sleep 1800  # 30 minutes

# 3. Try using expired token
curl -H "Authorization: Bearer $TOKEN" https://your-domain.com/api/auth/me
# Expected: 401 Unauthorized
```

---

## Security Metrics to Track

### Application Metrics
- Failed authentication attempts per hour
- 401/403 response rate
- Token expiration events
- Rate limit violations
- CSP violations (via report-uri)

### Infrastructure Metrics
- SSL certificate expiration date
- Dependency CVE count
- Security patch lag time
- Backup success rate
- Uptime percentage

### Incident Metrics
- Time to detection (TTD)
- Time to response (TTR)
- Time to resolution (TTResolution)
- Incident count per month
- False positive rate

---

## Sign-Off

This checklist must be reviewed and signed off by:

- [ ] **Development Lead:** _________________ Date: _______
- [ ] **Security Engineer:** _________________ Date: _______
- [ ] **DevOps Lead:** _________________ Date: _______
- [ ] **Product Manager:** _________________ Date: _______

**Deployment Authorization:**
- [ ] All CRITICAL items completed
- [ ] All HIGH PRIORITY items completed or documented exceptions
- [ ] Security testing completed successfully
- [ ] Team trained on security procedures

**Authorized for Production Deployment:** _________________ Date: _______

---

## Incident Contact Information

**Security Incidents:** security@openlearn.co (example)
**On-Call Engineer:** +57 XXX XXX XXXX
**Escalation Contact:** escalation@openlearn.co

**Emergency Procedures:** See `/docs/incident-response.md`

---

**Last Updated:** October 3, 2025
**Next Review:** Before each production deployment
**Owner:** Security Team
