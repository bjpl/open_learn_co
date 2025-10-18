# OpenLearn Weeks 2-3 Implementation Plan
**Strategic Planning Agent Report**
**Date:** 2025-10-16
**Planning Session:** Feature Implementation with Test-First Approach

---

## Executive Summary

This plan outlines a **test-driven implementation strategy** for Weeks 2-3, focusing on completing critical production features with comprehensive test coverage. The approach prioritizes **test-first development**, ensuring robust validation before implementation.

**Key Metrics:**
- **Current Test Coverage:** ~70-75% (estimated from project status)
- **Target Test Coverage:** 70-85% by end of Week 3
- **Critical Features:** 6 major items across 2 weeks
- **Testing Philosophy:** Write tests first, implement second, validate third

---

## Current State Analysis

### Existing Infrastructure ✅
```
Backend:
  ✓ 84 Python source files
  ✓ FastAPI application with lifecycle management
  ✓ 15+ news media scrapers
  ✓ 7+ government API clients
  ✓ Advanced NLP pipeline
  ✓ Database models (SQLAlchemy)
  ✓ Task scheduler (APScheduler)
  ✓ Comprehensive test suite (15 test files)

Frontend:
  ✓ 13 TypeScript components
  ✓ Next.js 14 with SSR
  ✓ 5 major pages
  ✓ React Query for data fetching
  ✓ Recharts & D3 visualization

Infrastructure:
  ✓ PostgreSQL + Redis + Elasticsearch
  ✓ Docker deployment scripts
  ✓ Railway + Vercel configs
  ✓ Health check endpoints
  ✓ Environment templates
```

### Identified Gaps 🔍
```
Data Pipelines:
  ⚠ Incomplete API client implementations
  ⚠ Missing integration tests for scrapers
  ⚠ No end-to-end pipeline validation

Avatar Upload:
  ❌ Feature not implemented
  ❌ No file upload validation
  ❌ No storage integration

Health Checks:
  ⚠ Placeholder implementations (deployment-checklist.md line 59)
  ⚠ No real database connectivity tests
  ⚠ No service dependency validation

Test Coverage:
  ⚠ Frontend tests missing (component, integration, E2E)
  ⚠ Security tests incomplete
  ⚠ Performance tests limited
  ⚠ Edge case coverage gaps
```

---

## WEEK 2: Core Feature Implementation (Test-First)

### Goal
Complete critical features with **test-driven development**, ensuring each component has comprehensive test coverage **before** implementation.

---

### Task 2.1: Data Pipeline Completion
**Priority:** P0 (Blocking)
**Estimated Effort:** 30-35 hours
**Test Coverage Target:** 90%+

#### Phase 1: Test Design (Day 1-2)
**Before writing any implementation code:**

1. **Pipeline Completion Tests**
   ```python
   # Location: backend/tests/integration/test_data_pipelines.py

   @pytest.mark.integration
   class TestDataPipelineCompletion:
       """Test complete data pipeline from scraping to storage"""

       async def test_scraper_to_database_pipeline(self):
           """Test scraper → NLP → database flow"""
           # GIVEN: A configured scraper and database
           # WHEN: Scraper runs and extracts data
           # THEN: Data should be processed and stored correctly

       async def test_api_client_to_cache_pipeline(self):
           """Test API client → cache → database flow"""
           # GIVEN: A configured API client
           # WHEN: API data is fetched
           # THEN: Data should be cached and persisted

       async def test_nlp_processing_pipeline(self):
           """Test text → NLP → enriched data flow"""
           # GIVEN: Raw text content
           # WHEN: NLP pipeline processes text
           # THEN: Entities, sentiment, topics extracted

       async def test_pipeline_error_handling(self):
           """Test pipeline resilience to failures"""
           # GIVEN: Simulated service failures
           # WHEN: Pipeline encounters errors
           # THEN: Graceful degradation and retry logic

       async def test_pipeline_performance(self):
           """Test pipeline throughput and latency"""
           # GIVEN: Batch of 100 articles
           # WHEN: Pipeline processes batch
           # THEN: Complete in < 30 seconds
   ```

2. **API Client Integration Tests**
   ```python
   # Location: backend/tests/integration/test_api_clients_integration.py

   @pytest.mark.integration
   class TestAPIClientIntegration:
       """Integration tests for government API clients"""

       async def test_dane_client_full_workflow(self):
           """DANE client: fetch → parse → validate → store"""

       async def test_banrep_client_rate_limiting(self):
           """BanRep client rate limit compliance"""

       async def test_secop_client_pagination(self):
           """SECOP client handles paginated results"""

       async def test_all_clients_health_checks(self):
           """All API clients respond to health checks"""

       async def test_client_authentication_failures(self):
           """Clients handle auth failures gracefully"""
   ```

3. **Scraper Validation Tests**
   ```python
   # Location: backend/tests/integration/test_scraper_validation.py

   @pytest.mark.integration
   class TestScraperValidation:
       """Validate all 15+ news scrapers"""

       @pytest.mark.parametrize("scraper_name", [
           "el_tiempo", "el_espectador", "semana", "la_republica",
           "portafolio", "dinero", "el_colombiano", "el_pais",
           "el_heraldo", "el_universal", "pulzo", "la_silla_vacia",
           "razon_publica", "colombia_check", "la_fm", "blu_radio"
       ])
       async def test_scraper_extracts_articles(self, scraper_name):
           """Each scraper extracts valid article data"""

       async def test_scraper_respects_robots_txt(self):
           """Scrapers respect robots.txt directives"""

       async def test_scraper_rate_limiting(self):
           """Scrapers adhere to rate limits"""

       async def test_scraper_error_recovery(self):
           """Scrapers recover from network errors"""
   ```

#### Phase 2: Implementation (Day 3-5)
**With tests written, implement features to pass tests:**

1. Complete missing API client implementations
2. Fix scraper edge cases
3. Implement pipeline orchestration
4. Add error handling and retry logic
5. Optimize pipeline performance

#### Phase 3: Validation (Day 6)
1. Run full test suite: `pytest backend/tests/integration/ -v`
2. Verify 90%+ coverage for pipeline code
3. Load test pipeline with 1000 articles
4. Document pipeline architecture

**Deliverables:**
- ✅ 3 comprehensive test files (~500 lines total)
- ✅ Pipeline orchestration service
- ✅ All 7 API clients fully operational
- ✅ All 15+ scrapers validated
- ✅ Pipeline documentation

---

### Task 2.2: Avatar Upload Feature
**Priority:** P1 (High)
**Estimated Effort:** 20-25 hours
**Test Coverage Target:** 95%+

#### Phase 1: Test Design (Day 1)
**Write tests before implementation:**

1. **File Upload Validation Tests**
   ```python
   # Location: backend/tests/api/test_avatar_upload.py

   @pytest.mark.asyncio
   class TestAvatarUpload:
       """Test avatar upload functionality"""

       async def test_upload_valid_image(self, client, auth_headers):
           """Upload valid JPEG/PNG image"""
           # GIVEN: Authenticated user with valid image file
           # WHEN: POST /api/users/avatar
           # THEN: 201 Created, avatar URL returned

       async def test_upload_invalid_file_type(self, client, auth_headers):
           """Reject non-image files (PDF, EXE, etc.)"""
           # GIVEN: Non-image file
           # WHEN: POST /api/users/avatar
           # THEN: 400 Bad Request, clear error message

       async def test_upload_oversized_file(self, client, auth_headers):
           """Reject files over size limit (5MB)"""
           # GIVEN: 10MB image file
           # WHEN: POST /api/users/avatar
           # THEN: 413 Payload Too Large

       async def test_upload_malicious_file(self, client, auth_headers):
           """Detect and reject malicious files"""
           # GIVEN: File with embedded script
           # WHEN: POST /api/users/avatar
           # THEN: 400 Bad Request, security error

       async def test_upload_unauthenticated(self, client):
           """Require authentication for upload"""
           # GIVEN: No auth token
           # WHEN: POST /api/users/avatar
           # THEN: 401 Unauthorized

       async def test_delete_avatar(self, client, auth_headers):
           """Delete existing avatar"""
           # GIVEN: User with existing avatar
           # WHEN: DELETE /api/users/avatar
           # THEN: 204 No Content, avatar removed
   ```

2. **Storage Integration Tests**
   ```python
   # Location: backend/tests/services/test_avatar_storage.py

   @pytest.mark.asyncio
   class TestAvatarStorage:
       """Test avatar storage backend"""

       async def test_store_avatar_in_s3(self):
           """Store avatar in S3/local storage"""

       async def test_generate_unique_filename(self):
           """Generate collision-free filenames"""

       async def test_generate_presigned_url(self):
           """Generate secure URLs for avatars"""

       async def test_cleanup_old_avatars(self):
           """Clean up replaced avatars"""

       async def test_storage_failure_handling(self):
           """Handle storage service failures"""
   ```

3. **Image Processing Tests**
   ```python
   # Location: backend/tests/services/test_image_processing.py

   @pytest.mark.asyncio
   class TestImageProcessing:
       """Test image validation and processing"""

       async def test_validate_image_format(self):
           """Validate JPEG/PNG/WEBP formats"""

       async def test_resize_large_images(self):
           """Resize images to 500x500 max"""

       async def test_strip_exif_data(self):
           """Remove EXIF/metadata for privacy"""

       async def test_detect_invalid_images(self):
           """Detect corrupted/invalid images"""
   ```

#### Phase 2: Implementation (Day 2-4)
1. Implement avatar upload endpoint
2. Integrate with storage backend (S3 or local)
3. Add image validation and processing
4. Implement file cleanup logic
5. Add rate limiting for uploads

#### Phase 3: Validation (Day 5)
1. Run avatar test suite: `pytest backend/tests/ -k avatar -v`
2. Verify 95%+ coverage
3. Test with various file types and sizes
4. Security scan with malicious files

**Deliverables:**
- ✅ 3 test files (~300 lines total)
- ✅ Avatar upload API endpoint
- ✅ Storage integration (S3/local)
- ✅ Image processing service
- ✅ Upload documentation

---

### Task 2.3: Comprehensive Health Checks
**Priority:** P0 (Blocking for Production)
**Estimated Effort:** 15-20 hours
**Test Coverage Target:** 100%

#### Phase 1: Test Design (Day 1)
**Critical: Health checks MUST be tested thoroughly**

1. **Health Check Endpoint Tests**
   ```python
   # Location: backend/tests/api/test_health_checks.py

   @pytest.mark.asyncio
   class TestHealthChecks:
       """Test health check endpoints"""

       async def test_liveness_probe(self, client):
           """Liveness probe always returns 200"""
           # GIVEN: Running application
           # WHEN: GET /health/live
           # THEN: 200 OK immediately (no dependency checks)

       async def test_readiness_probe_all_healthy(self, client):
           """Readiness with all dependencies healthy"""
           # GIVEN: All services (DB, Redis, ES) running
           # WHEN: GET /health/ready
           # THEN: 200 OK with all checks passing

       async def test_readiness_probe_database_down(self, client):
           """Readiness when database is down"""
           # GIVEN: Database connection fails
           # WHEN: GET /health/ready
           # THEN: 503 Service Unavailable, database: false

       async def test_readiness_probe_redis_down(self, client):
           """Readiness when Redis is down"""
           # GIVEN: Redis connection fails
           # WHEN: GET /health/ready
           # THEN: 503 Service Unavailable, redis: false

       async def test_readiness_probe_elasticsearch_down(self, client):
           """Readiness when Elasticsearch is down"""
           # GIVEN: Elasticsearch connection fails
           # WHEN: GET /health/ready
           # THEN: 503 Service Unavailable, elasticsearch: false

       async def test_health_check_timeout(self, client):
           """Health checks timeout after 5 seconds"""
           # GIVEN: Slow dependency response
           # WHEN: GET /health/ready
           # THEN: Returns within 5 seconds with timeout error
   ```

2. **Dependency Health Tests**
   ```python
   # Location: backend/tests/database/test_health_checks.py

   @pytest.mark.asyncio
   class TestDatabaseHealth:
       """Test database health checks"""

       async def test_database_connectivity(self):
           """Verify database connection works"""

       async def test_database_query_performance(self):
           """Check database response time < 100ms"""

       async def test_database_connection_pool(self):
           """Verify connection pool is healthy"""

       async def test_database_disk_space(self):
           """Check database has sufficient disk space"""
   ```

3. **Service Health Tests**
   ```python
   # Location: backend/tests/services/test_health_monitoring.py

   @pytest.mark.asyncio
   class TestServiceHealth:
       """Test service-level health monitoring"""

       async def test_scheduler_health(self):
           """Verify scheduler is running jobs"""

       async def test_scraper_health(self):
           """Verify scrapers are functioning"""

       async def test_api_client_health(self):
           """Verify API clients are accessible"""
   ```

#### Phase 2: Implementation (Day 2-3)
**Fix deployment-checklist.md line 59 placeholders:**

1. Implement real database health check
2. Implement Redis health check
3. Implement Elasticsearch health check
4. Add timeout handling (5s max)
5. Implement detailed health status endpoint

**Implementation:**
```python
# Location: backend/app/api/monitoring.py

async def check_database() -> Dict[str, Any]:
    """Real database health check"""
    try:
        from app.database import engine
        from sqlalchemy import text
        import time

        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000

        # Check connection pool
        pool_status = await get_pool_status()

        return {
            "healthy": True,
            "latency_ms": round(latency, 2),
            "pool_size": pool_status["size"],
            "pool_overflow": pool_status["overflow"]
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }

async def check_redis() -> Dict[str, Any]:
    """Real Redis health check"""
    try:
        from app.core.cache import cache_manager
        import time

        start = time.time()
        await cache_manager.ping()
        latency = (time.time() - start) * 1000

        # Get Redis info
        info = await cache_manager.info()

        return {
            "healthy": True,
            "latency_ms": round(latency, 2),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }

async def check_elasticsearch() -> Dict[str, Any]:
    """Real Elasticsearch health check"""
    try:
        from app.search.elasticsearch_client import get_elasticsearch_client
        import time

        start = time.time()
        es_client = await get_elasticsearch_client()
        health = await es_client.health_check()
        latency = (time.time() - start) * 1000

        return {
            "healthy": health.get("healthy", False),
            "status": health.get("status", "unknown"),
            "latency_ms": round(latency, 2),
            "number_of_nodes": health.get("number_of_nodes", 0)
        }
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }
```

#### Phase 3: Validation (Day 4)
1. Run health check tests: `pytest backend/tests/ -k health -v`
2. Verify 100% coverage for health checks
3. Test with all dependencies up
4. Test with dependencies down (one at a time)
5. Test timeout behavior
6. Load test health endpoints (10,000 requests)

**Deliverables:**
- ✅ 3 test files (~250 lines total)
- ✅ Real health check implementations
- ✅ Detailed health status endpoint
- ✅ Health monitoring documentation
- ✅ Kubernetes readiness/liveness probes ready

---

## WEEK 3: Testing & Production Readiness

### Goal
Achieve **70-85% test coverage** across the entire codebase and prepare comprehensive security and deployment validation.

---

### Task 3.1: Coverage Strategy & Expansion
**Priority:** P1 (High)
**Estimated Effort:** 35-40 hours
**Coverage Target:** 70-85%

#### Phase 1: Coverage Analysis (Day 1)
**Identify untested modules:**

1. **Generate Coverage Report**
   ```bash
   # Backend coverage
   pytest backend/tests/ --cov=backend/app --cov-report=html --cov-report=term

   # Identify gaps
   coverage report --show-missing --skip-covered
   ```

2. **Priority Matrix**
   ```
   High Risk, Low Coverage (PRIORITY 1):
   - Authentication logic (auth.py)
   - Payment processing (if any)
   - Data export (export.py)
   - Security middleware

   Medium Risk, Low Coverage (PRIORITY 2):
   - Analysis endpoints
   - Scheduler jobs
   - Cache middleware
   - Preferences management

   Low Risk, Low Coverage (PRIORITY 3):
   - Utility functions
   - Configuration loading
   - Logging helpers
   ```

#### Phase 2: Frontend Testing Setup (Day 2)
**Currently MISSING all frontend tests:**

1. **Component Tests (Jest + React Testing Library)**
   ```typescript
   // Location: frontend/__tests__/components/Dashboard.test.tsx

   describe('Dashboard Component', () => {
     it('renders loading state initially', () => {
       // GIVEN: Dashboard component
       // WHEN: Component mounts
       // THEN: Loading spinner displayed
     });

     it('fetches and displays news articles', async () => {
       // GIVEN: Mocked API response
       // WHEN: Data loads
       // THEN: Articles displayed in grid
     });

     it('handles API errors gracefully', async () => {
       // GIVEN: API returns error
       // WHEN: Component renders
       // THEN: Error message displayed
     });

     it('filters articles by source', async () => {
       // GIVEN: Articles from multiple sources
       // WHEN: User selects source filter
       // THEN: Only matching articles displayed
     });
   });
   ```

2. **Integration Tests (Playwright)**
   ```typescript
   // Location: frontend/e2e/dashboard-flow.spec.ts

   test.describe('Dashboard Flow', () => {
     test('complete dashboard interaction', async ({ page }) => {
       // Navigate to dashboard
       await page.goto('/dashboard');

       // Verify charts load
       await expect(page.locator('.recharts-wrapper')).toBeVisible();

       // Interact with filters
       await page.click('[data-testid="source-filter"]');
       await page.click('text=El Tiempo');

       // Verify filtered results
       await expect(page.locator('.article-card')).toHaveCount(5);
     });
   });
   ```

3. **Setup Jest Configuration**
   ```javascript
   // Location: frontend/jest.config.js

   module.exports = {
     preset: 'ts-jest',
     testEnvironment: 'jsdom',
     setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
     moduleNameMapper: {
       '^@/(.*)$': '<rootDir>/src/$1',
     },
     collectCoverageFrom: [
       'src/**/*.{ts,tsx}',
       '!src/**/*.d.ts',
       '!src/**/*.stories.tsx',
     ],
     coverageThresholds: {
       global: {
         branches: 70,
         functions: 70,
         lines: 70,
         statements: 70,
       },
     },
   };
   ```

#### Phase 3: Backend Test Expansion (Day 3-5)
**Write tests for uncovered modules:**

1. **Authentication Tests**
   ```python
   # Location: backend/tests/api/test_auth_comprehensive.py

   @pytest.mark.asyncio
   class TestAuthenticationSecurity:
       """Comprehensive authentication security tests"""

       async def test_password_hashing(self):
           """Passwords are hashed with bcrypt"""

       async def test_jwt_token_generation(self):
           """JWT tokens are properly signed"""

       async def test_jwt_token_validation(self):
           """Invalid tokens are rejected"""

       async def test_token_expiration(self):
           """Expired tokens are rejected"""

       async def test_refresh_token_rotation(self):
           """Refresh tokens are rotated on use"""

       async def test_brute_force_protection(self):
           """Login rate limiting prevents brute force"""

       async def test_password_reset_flow(self):
           """Password reset tokens are secure"""
   ```

2. **Edge Case Tests**
   ```python
   # Location: backend/tests/edge_cases/test_boundary_conditions.py

   @pytest.mark.asyncio
   class TestBoundaryConditions:
       """Test edge cases and boundary conditions"""

       async def test_empty_database_queries(self):
           """Handle empty result sets gracefully"""

       async def test_maximum_page_size(self):
           """Reject page sizes over limit (100)"""

       async def test_invalid_date_ranges(self):
           """Validate date range inputs"""

       async def test_concurrent_updates(self):
           """Handle concurrent update conflicts"""

       async def test_unicode_handling(self):
           """Properly handle Unicode characters"""
   ```

3. **Error Handling Tests**
   ```python
   # Location: backend/tests/middleware/test_error_handling.py

   @pytest.mark.asyncio
   class TestErrorHandling:
       """Test error handling middleware"""

       async def test_404_not_found(self, client):
           """404 returns proper error format"""

       async def test_500_internal_error(self, client):
           """500 errors are logged and formatted"""

       async def test_validation_errors(self, client):
           """422 validation errors include field details"""

       async def test_rate_limit_errors(self, client):
           """429 rate limit errors include retry-after"""
   ```

#### Phase 4: Validation (Day 6-7)
1. Run full test suite: `pytest backend/tests/ -v`
2. Generate coverage report: `pytest --cov --cov-report=html`
3. Run frontend tests: `npm test`
4. Run E2E tests: `npx playwright test`
5. Verify 70-85% coverage achieved
6. Document coverage gaps and exceptions

**Deliverables:**
- ✅ Frontend test setup (Jest + Playwright)
- ✅ 10+ new backend test files
- ✅ 5+ frontend component test files
- ✅ 3+ E2E test scenarios
- ✅ Coverage report achieving 70-85%
- ✅ Testing documentation

---

### Task 3.2: Security Audit & Test Plan
**Priority:** P0 (Blocking for Production)
**Estimated Effort:** 25-30 hours
**Security Test Coverage:** 100%

#### Phase 1: Security Test Design (Day 1-2)
**Security is non-negotiable for production:**

1. **Authentication/Authorization Tests**
   ```python
   # Location: backend/tests/security/test_authentication_security.py

   @pytest.mark.security
   class TestAuthenticationSecurity:
       """Security tests for authentication"""

       async def test_weak_password_rejected(self):
           """Reject passwords shorter than 12 characters"""

       async def test_common_password_rejected(self):
           """Reject common passwords (top 10,000 list)"""

       async def test_password_complexity_requirements(self):
           """Require uppercase, lowercase, number, symbol"""

       async def test_account_lockout_after_failures(self):
           """Lock account after 5 failed login attempts"""

       async def test_session_timeout(self):
           """Sessions expire after 30 minutes inactivity"""

       async def test_concurrent_session_limit(self):
           """Limit user to 5 concurrent sessions"""
   ```

2. **Input Validation Tests**
   ```python
   # Location: backend/tests/security/test_input_validation.py

   @pytest.mark.security
   class TestInputValidation:
       """Test input validation security"""

       async def test_sql_injection_prevention(self):
           """Reject SQL injection attempts"""
           # Test with: ' OR '1'='1

       async def test_xss_prevention(self):
           """Sanitize XSS attempts"""
           # Test with: <script>alert('XSS')</script>

       async def test_path_traversal_prevention(self):
           """Prevent path traversal attacks"""
           # Test with: ../../etc/passwd

       async def test_command_injection_prevention(self):
           """Prevent command injection"""
           # Test with: ; rm -rf /

       async def test_xxe_prevention(self):
           """Prevent XML External Entity attacks"""

       async def test_ldap_injection_prevention(self):
           """Prevent LDAP injection"""
   ```

3. **API Security Tests**
   ```python
   # Location: backend/tests/security/test_api_security.py

   @pytest.mark.security
   class TestAPISecurity:
       """Test API security measures"""

       async def test_cors_headers(self, client):
           """CORS headers properly configured"""

       async def test_security_headers(self, client):
           """Security headers present (HSTS, CSP, etc.)"""

       async def test_rate_limiting(self, client):
           """Rate limiting enforced (100 req/min)"""

       async def test_authentication_required(self, client):
           """Protected endpoints require auth"""

       async def test_csrf_protection(self, client):
           """CSRF tokens validated"""

       async def test_clickjacking_prevention(self, client):
           """X-Frame-Options header present"""
   ```

4. **Sensitive Data Tests**
   ```python
   # Location: backend/tests/security/test_sensitive_data.py

   @pytest.mark.security
   class TestSensitiveData:
       """Test sensitive data handling"""

       async def test_passwords_not_in_logs(self):
           """Passwords never logged"""

       async def test_tokens_not_in_error_messages(self):
           """Auth tokens not exposed in errors"""

       async def test_pii_redaction_in_logs(self):
           """PII redacted from logs"""

       async def test_secure_cookie_flags(self):
           """Cookies have Secure and HttpOnly flags"""

       async def test_https_enforcement(self):
           """HTTP redirects to HTTPS"""
   ```

#### Phase 2: Security Tool Integration (Day 3)
**Automate security scanning:**

1. **Install Security Tools**
   ```bash
   # Python security scanning
   pip install bandit safety semgrep

   # JavaScript security scanning
   npm install --save-dev snyk eslint-plugin-security
   ```

2. **Configure Security Scans**
   ```yaml
   # Location: .github/workflows/security-scan.yml

   name: Security Scan
   on: [push, pull_request]

   jobs:
     security:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Run Bandit
           run: bandit -r backend/ -f json -o bandit-report.json

         - name: Run Safety
           run: safety check --json

         - name: Run Semgrep
           run: semgrep --config=auto backend/

         - name: Run npm audit
           run: cd frontend && npm audit --audit-level=moderate
   ```

3. **Create Security Checklist**
   ```markdown
   # Location: docs/security-checklist.md

   ## Pre-Deployment Security Checklist

   ### Code Security
   - [ ] Bandit scan passes (0 high/medium issues)
   - [ ] Safety check passes (0 vulnerabilities)
   - [ ] Semgrep scan passes
   - [ ] npm audit passes
   - [ ] All security tests pass

   ### Configuration Security
   - [ ] DEBUG=False in production
   - [ ] SECRET_KEY is random and secure
   - [ ] Database passwords are strong (20+ chars)
   - [ ] API keys are in environment variables
   - [ ] CORS origins are production domains only

   ### Infrastructure Security
   - [ ] HTTPS enforced
   - [ ] Security headers configured
   - [ ] Firewall rules configured
   - [ ] SSH key-based authentication only
   - [ ] Fail2ban configured
   ```

#### Phase 3: Penetration Testing (Day 4-5)
**Manual security testing:**

1. **OWASP Top 10 Testing**
   ```
   A01: Broken Access Control
     - Test horizontal privilege escalation
     - Test vertical privilege escalation
     - Test direct object references

   A02: Cryptographic Failures
     - Test encryption at rest
     - Test encryption in transit
     - Test key management

   A03: Injection
     - SQL injection testing
     - Command injection testing
     - LDAP injection testing

   A04: Insecure Design
     - Review threat model
     - Test business logic flaws

   A05: Security Misconfiguration
     - Test default credentials
     - Test error handling
     - Test unnecessary features

   A06: Vulnerable Components
     - Audit dependencies
     - Check for outdated libraries

   A07: Authentication Failures
     - Test password policies
     - Test session management
     - Test credential recovery

   A08: Data Integrity Failures
     - Test deserialization
     - Test CI/CD security

   A09: Logging Failures
     - Test log integrity
     - Test log monitoring

   A10: SSRF
     - Test URL validation
     - Test webhook security
   ```

2. **Automated Penetration Testing**
   ```bash
   # OWASP ZAP scanning
   docker run -t owasp/zap2docker-stable zap-baseline.py \
     -t https://api.yourdomain.com \
     -r zap-report.html

   # Nikto web scanner
   nikto -h https://api.yourdomain.com -output nikto-report.txt
   ```

#### Phase 4: Security Documentation (Day 6)
1. Document security architecture
2. Create incident response plan
3. Write security best practices guide
4. Create security training materials

**Deliverables:**
- ✅ 4 comprehensive security test files (~400 lines)
- ✅ Automated security scanning in CI/CD
- ✅ Security audit report
- ✅ Penetration testing results
- ✅ Security documentation
- ✅ Incident response plan

---

### Task 3.3: Production Deployment Validation
**Priority:** P0 (Blocking for Launch)
**Estimated Effort:** 20-25 hours
**Test Coverage:** 100% of deployment process

#### Phase 1: Pre-Deployment Test Suite (Day 1-2)
**Validate BEFORE production deployment:**

1. **Deployment Smoke Tests**
   ```python
   # Location: backend/tests/deployment/test_production_readiness.py

   @pytest.mark.deployment
   class TestProductionReadiness:
       """Pre-deployment validation tests"""

       def test_debug_mode_disabled(self):
           """Verify DEBUG=False in production"""
           assert settings.DEBUG is False

       def test_secret_key_is_secure(self):
           """Verify SECRET_KEY is not default"""
           assert settings.SECRET_KEY != "changeme"
           assert len(settings.SECRET_KEY) >= 32

       def test_database_url_is_production(self):
           """Verify database URL is production"""
           assert "localhost" not in settings.DATABASE_URL

       def test_cors_origins_are_production(self):
           """Verify CORS origins are production domains"""
           for origin in settings.CORS_ORIGINS:
               assert "localhost" not in origin

       def test_all_required_env_vars_set(self):
           """Verify all required environment variables"""
           required = [
               "DATABASE_URL",
               "REDIS_URL",
               "SECRET_KEY",
               "CORS_ORIGINS",
           ]
           for var in required:
               assert getattr(settings, var, None) is not None
   ```

2. **Integration Test Suite**
   ```python
   # Location: backend/tests/deployment/test_production_integration.py

   @pytest.mark.deployment
   class TestProductionIntegration:
       """Production integration tests"""

       async def test_database_migrations_applied(self):
           """Verify all migrations are applied"""

       async def test_database_indexes_created(self):
           """Verify performance indexes exist"""

       async def test_scheduler_jobs_registered(self):
           """Verify all scheduled jobs are loaded"""

       async def test_redis_cache_working(self):
           """Verify Redis cache is functional"""

       async def test_elasticsearch_indices_created(self):
           """Verify search indices exist"""
   ```

3. **Load Testing Suite**
   ```python
   # Location: backend/tests/deployment/locustfile.py

   from locust import HttpUser, task, between

   class OpenLearnUser(HttpUser):
       wait_time = between(1, 3)

       @task(10)
       def view_dashboard(self):
           """Simulate dashboard views"""
           self.client.get("/api/articles")

       @task(5)
       def search_articles(self):
           """Simulate search queries"""
           self.client.get("/api/search?q=colombia")

       @task(2)
       def run_analysis(self):
           """Simulate analysis requests"""
           self.client.post("/api/analysis/trends")
   ```

#### Phase 2: Post-Deployment Validation (Day 3)
**Validate AFTER production deployment:**

1. **Production Smoke Tests**
   ```bash
   # Location: scripts/production/smoke_tests.sh

   #!/bin/bash

   API_URL="https://api.yourdomain.com"

   # Health checks
   curl -f $API_URL/health/live || exit 1
   curl -f $API_URL/health/ready || exit 1

   # API endpoints
   curl -f $API_URL/docs || exit 1
   curl -f $API_URL/api/scraping/status || exit 1

   # Security headers
   curl -I $API_URL | grep "Strict-Transport-Security" || exit 1
   curl -I $API_URL | grep "X-Frame-Options" || exit 1

   # Response times
   response_time=$(curl -o /dev/null -s -w '%{time_total}' $API_URL/health/live)
   if (( $(echo "$response_time > 1.0" | bc -l) )); then
       echo "Response time too slow: ${response_time}s"
       exit 1
   fi

   echo "All smoke tests passed!"
   ```

2. **Monitoring Validation**
   ```python
   # Location: backend/tests/deployment/test_monitoring.py

   @pytest.mark.deployment
   class TestMonitoring:
       """Validate monitoring is functional"""

       async def test_prometheus_metrics_endpoint(self):
           """Verify Prometheus metrics are exposed"""

       async def test_sentry_error_reporting(self):
           """Verify Sentry captures errors"""

       async def test_log_aggregation(self):
           """Verify logs are being collected"""

       async def test_alerting_rules(self):
           """Verify alert rules are configured"""
   ```

3. **Rollback Testing**
   ```bash
   # Location: scripts/production/test_rollback.sh

   #!/bin/bash

   # Test rollback procedure in staging

   # 1. Deploy new version
   ./scripts/production/deploy.sh

   # 2. Verify deployment
   ./scripts/production/smoke_tests.sh

   # 3. Simulate failure
   # (manually introduce breaking change)

   # 4. Execute rollback
   ./scripts/production/rollback.sh

   # 5. Verify rollback success
   ./scripts/production/smoke_tests.sh
   ```

#### Phase 3: Continuous Deployment Setup (Day 4)
**Automate deployment pipeline:**

1. **CI/CD Pipeline**
   ```yaml
   # Location: .github/workflows/deploy-production.yml

   name: Production Deployment

   on:
     push:
       tags:
         - 'v*'

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Run Tests
           run: pytest backend/tests/ -v --cov

         - name: Security Scan
           run: |
             bandit -r backend/
             safety check

         - name: Check Coverage
           run: |
             coverage report --fail-under=75

     deploy:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - name: Deploy to Production
           run: |
             ./scripts/production/deploy.sh

         - name: Run Smoke Tests
           run: |
             ./scripts/production/smoke_tests.sh

         - name: Notify Team
           if: success()
           run: |
             curl -X POST $SLACK_WEBHOOK \
               -d '{"text": "✅ Production deployment successful"}'
   ```

#### Phase 4: Documentation (Day 5)
1. Update deployment checklist
2. Document rollback procedures
3. Create runbook for common issues
4. Write post-deployment validation guide

**Deliverables:**
- ✅ 3 deployment test files (~300 lines)
- ✅ Load testing suite (Locust)
- ✅ Smoke test scripts
- ✅ CI/CD pipeline configuration
- ✅ Deployment documentation
- ✅ Runbook for production operations

---

## Success Metrics

### Week 2 Checkpoint
```
✓ Data pipelines fully operational
✓ All 7 API clients tested and validated
✓ All 15+ scrapers tested and validated
✓ Avatar upload feature complete with 95%+ coverage
✓ Health checks implemented with 100% coverage
✓ 90%+ test coverage for new features
```

### Week 3 Checkpoint
```
✓ Test coverage 70-85% across entire codebase
✓ Frontend tests: 70%+ coverage
✓ Backend tests: 85%+ coverage
✓ Security audit completed with no critical issues
✓ Deployment validation suite complete
✓ Production readiness verified
```

---

## Risk Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Test coverage goal not met | Medium | High | Prioritize high-risk modules, extend timeline if needed |
| Health check implementation blocked | Low | Critical | Allocate senior dev, pair programming |
| Avatar upload storage issues | Medium | Medium | Have S3 and local storage options ready |
| Security vulnerabilities found | Medium | Critical | Schedule immediate fixes, delay launch if needed |
| Deployment automation fails | Low | High | Test thoroughly in staging, have manual fallback |

### Schedule Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Week 2 overruns into Week 3 | Medium | Medium | Buffer days built into Week 3 plan |
| Developer availability | Low | High | Cross-train team members on critical tasks |
| Dependencies block progress | Low | Medium | Identify dependencies early, have alternatives |

---

## Resource Allocation

### Team Requirements
```
Week 2:
  Backend Developer A: Data pipelines (full-time)
  Backend Developer B: Avatar upload (full-time)
  Backend Developer C: Health checks (50%)
  QA Engineer: Test design and validation (full-time)

Week 3:
  Backend Developer A: Backend test expansion (full-time)
  Frontend Developer: Frontend tests (full-time)
  Security Engineer: Security audit (full-time)
  DevOps Engineer: Deployment validation (full-time)
  QA Engineer: Test validation (full-time)
```

### Tool Requirements
```
Testing:
  - pytest, pytest-cov
  - Jest, React Testing Library
  - Playwright
  - Locust (load testing)

Security:
  - Bandit, Safety, Semgrep
  - OWASP ZAP
  - Snyk

Monitoring:
  - Prometheus, Grafana
  - Sentry
  - CloudWatch / Datadog
```

---

## Timeline

```
WEEK 2: Core Features
═══════════════════════════════════════════════
Day 1-2:  Test design for data pipelines
Day 3-5:  Implement pipelines to pass tests
Day 6:    Validate pipeline implementation

Day 1:    Test design for avatar upload
Day 2-4:  Implement avatar upload to pass tests
Day 5:    Validate avatar implementation

Day 1:    Test design for health checks
Day 2-3:  Implement health checks to pass tests
Day 4:    Validate health check implementation

WEEK 3: Testing & Production
═══════════════════════════════════════════════
Day 1:    Coverage analysis and planning
Day 2:    Frontend test setup
Day 3-5:  Backend test expansion
Day 6-7:  Coverage validation

Day 1-2:  Security test design
Day 3:    Security tool integration
Day 4-5:  Penetration testing
Day 6:    Security documentation

Day 1-2:  Pre-deployment test suite
Day 3:    Post-deployment validation
Day 4:    CI/CD pipeline setup
Day 5:    Deployment documentation
```

---

## Next Steps

### Immediate Actions (This Week)
1. Review and approve this plan with stakeholders
2. Assign team members to tasks
3. Set up project tracking (Jira/Linear)
4. Begin Week 2 Day 1: Data pipeline test design
5. Schedule daily standups and weekly reviews

### Communication Plan
```
Daily:    15-min standup (9:00 AM)
Weekly:   Sprint planning (Monday 10:00 AM)
Weekly:   Demo and retrospective (Friday 3:00 PM)
Ad-hoc:   Slack #openlearn-dev for questions
```

---

## Appendix: Test-First Development Guidelines

### The TDD Cycle
```
1. RED: Write a failing test
   - Clearly define expected behavior
   - Test should fail initially (no implementation yet)

2. GREEN: Write minimal code to pass test
   - Implement just enough to make test pass
   - Don't add extra features

3. REFACTOR: Improve code quality
   - Optimize implementation
   - Remove duplication
   - Improve readability

4. REPEAT: Move to next test
```

### Test Naming Convention
```python
def test_<feature>_<scenario>_<expected_result>(self):
    """
    GIVEN: <preconditions>
    WHEN: <action>
    THEN: <expected outcome>
    """
```

### Test Organization
```
backend/tests/
  ├── api/              # API endpoint tests
  ├── integration/      # Integration tests
  ├── services/         # Service layer tests
  ├── security/         # Security tests
  ├── deployment/       # Deployment tests
  └── edge_cases/       # Edge case tests

frontend/__tests__/
  ├── components/       # Component tests
  ├── integration/      # Integration tests
  └── e2e/              # End-to-end tests
```

---

**Plan Status:** Ready for Execution
**Approval Required:** Technical Lead, Product Owner
**Next Review:** End of Week 2 (Checkpoint Meeting)
