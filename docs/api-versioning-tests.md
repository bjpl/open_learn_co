# API Versioning Test Suite

## Overview
This document provides comprehensive tests for the API versioning implementation for OpenLearn Colombia.

## Backend Changes Summary

### 1. Main Application (`backend/app/main.py`)
- Created `api_v1_router` to handle all versioned endpoints
- All routers now mounted under `/api/v1` prefix
- Added `APIVersionMiddleware` to inject `X-API-Version: 1.0.0` header in all responses
- Implemented backward compatibility redirect from `/api/*` to `/api/v1/*` with 301 status
- Updated OpenAPI docs URLs to `/api/v1/docs`, `/api/v1/redoc`, `/api/v1/openapi.json`

### 2. Avatar Router (`backend/app/api/avatar.py`)
- Changed prefix from `/api/avatars` to `/avatars` (will be combined with v1 prefix)

### 3. Preferences Router (`backend/app/api/preferences.py`)
- Removed `/api` prefix from all routes:
  - `/api/preferences` → `/preferences`
  - `/api/users/me/account` → `/users/me/account`
  - `/api/users/me/progress` → `/users/me/progress`
  - `/api/preferences/export` → `/preferences/export`
  - `/api/preferences/health` → `/preferences/health`

## Frontend Changes Summary

### Files Updated with `/api/v1/` Prefix

1. **News Page** (`frontend/src/app/news/page.tsx`)
   - `/api/scraping/content/simple` → `/api/v1/scraping/content/simple`

2. **Analytics Page** (`frontend/src/app/analytics/page.tsx`)
   - `/api/scraping/content/simple` → `/api/v1/scraping/content/simple`

3. **Sources Page** (`frontend/src/app/sources/page.tsx`)
   - `/api/scraping/content/simple` → `/api/v1/scraping/content/simple`
   - `/api/scraping/trigger/{endpoint}` → `/api/v1/scraping/trigger/{endpoint}`

4. **Homepage** (`frontend/src/app/page.tsx`)
   - `/api/scraping/content/simple` → `/api/v1/scraping/content/simple`

5. **Trends Page** (`frontend/src/app/trends/page.tsx`)
   - `/api/scraping/content/simple` → `/api/v1/scraping/content/simple`

6. **Auth Hook** (`frontend/src/hooks/useAuth.tsx`)
   - `/api/auth/me` → `/api/v1/auth/me`
   - `/api/auth/token` → `/api/v1/auth/token`
   - `/api/auth/logout` → `/api/v1/auth/logout`

7. **Data Management** (`frontend/src/components/preferences/DataManagement.tsx`)
   - `/api/users/me/progress` → `/api/v1/users/me/progress`
   - `/api/users/me/account` → `/api/v1/users/me/account`

## Test Cases

### Backend Tests

#### 1. Root Endpoint
```bash
curl http://localhost:8002/
```
**Expected Response:**
```json
{
  "platform": "Colombia Intelligence & Language Learning",
  "version": "1.0.0",
  "api_version": "v1",
  "status": "operational",
  "endpoints": {
    "docs": "/docs",
    "api_v1": "/api/v1",
    "scraping": "/api/v1/scraping",
    "analysis": "/api/v1/analysis",
    "auth": "/api/v1/auth",
    "health": "/api/v1/health",
    "preferences": "/api/v1/preferences"
  }
}
```

#### 2. Versioned Health Check
```bash
curl -i http://localhost:8002/api/v1/health
```
**Expected Response Headers:**
```
HTTP/1.1 200 OK
X-API-Version: 1.0.0
Content-Type: application/json
```
**Expected Response Body:**
```json
{
  "status": "ok",
  "service": "openlearn"
}
```

#### 3. Backward Compatibility - Legacy Endpoint Redirect
```bash
curl -i http://localhost:8002/api/health
```
**Expected Response:**
```
HTTP/1.1 301 Moved Permanently
Location: /api/v1/health
X-API-Version: 1.0.0
```

#### 4. Versioned Scraping Endpoint
```bash
curl -i http://localhost:8002/api/v1/scraping/content/simple?limit=10
```
**Expected Response Headers:**
```
HTTP/1.1 200 OK
X-API-Version: 1.0.0
Content-Type: application/json
```

#### 5. Versioned Auth Endpoint
```bash
curl -i -X POST http://localhost:8002/api/v1/auth/token \
  -F "username=test@example.com" \
  -F "password=testpass123"
```
**Expected Response Headers:**
```
HTTP/1.1 200 OK (or 401 if credentials invalid)
X-API-Version: 1.0.0
Content-Type: application/json
```

#### 6. OpenAPI Documentation
```bash
# New versioned docs URL
curl -i http://localhost:8002/api/v1/docs
```
**Expected:** HTML page with Swagger UI

```bash
# OpenAPI JSON schema
curl http://localhost:8002/api/v1/openapi.json | jq '.info.version'
```
**Expected:** `"1.0.0"`

#### 7. Preferences Endpoints
```bash
# Health check
curl -i http://localhost:8002/api/v1/preferences/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "preferences",
  "timestamp": "2025-11-20T..."
}
```

#### 8. Avatar Endpoints
```bash
# GET avatar (requires auth)
curl -i -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8002/api/v1/avatars/USER_ID
```

### Frontend Tests

#### 1. News Page API Call
Open browser dev tools, navigate to `/news`, check Network tab:
- **URL Called:** `http://localhost:8002/api/v1/scraping/content/simple?limit=10`
- **Response Headers:** Should include `X-API-Version: 1.0.0`

#### 2. Authentication Flow
1. Navigate to `/login`
2. Enter credentials
3. Check Network tab for:
   - **URL Called:** `http://localhost:8002/api/v1/auth/token`
   - **Response Headers:** Should include `X-API-Version: 1.0.0`

#### 3. Sources Page Scraper Trigger
1. Navigate to `/sources`
2. Click "Run Scraper" button
3. Check Network tab for:
   - **URL Called:** `http://localhost:8002/api/v1/scraping/trigger/El%20Tiempo`
   - **Response Headers:** Should include `X-API-Version: 1.0.0`

## Verification Checklist

### Backend
- [x] All routes accessible via `/api/v1/` prefix
- [x] `X-API-Version: 1.0.0` header present in all responses
- [x] Legacy `/api/*` routes redirect to `/api/v1/*` with 301 status
- [x] OpenAPI docs available at `/api/v1/docs`
- [x] OpenAPI JSON schema at `/api/v1/openapi.json`
- [x] Root endpoint documents v1 API structure

### Frontend
- [x] All API calls updated to use `/api/v1/` prefix
- [x] Auth endpoints use versioned paths
- [x] Scraping endpoints use versioned paths
- [x] User management endpoints use versioned paths

## Breaking Changes
**None** - Full backward compatibility maintained via 301 redirects.

## Future Considerations

### API v2 Migration Path
When introducing breaking changes in the future:

1. Create new `api_v2_router` in `main.py`
2. Keep `api_v1_router` running for legacy clients
3. Update middleware to check version from:
   - URL path (`/api/v2/*`)
   - Accept header (`Accept: application/vnd.openlearn.v2+json`)
   - Custom header (`X-API-Version: 2.0.0`)

### Deprecation Strategy
1. Add deprecation warnings to v1 responses:
   ```json
   {
     "deprecated": true,
     "deprecation_date": "2026-06-01",
     "migration_guide": "/docs/api/v1-to-v2-migration"
   }
   ```
2. Set sunset date in HTTP header:
   ```
   Sunset: Sat, 01 Jun 2026 00:00:00 GMT
   ```
3. Provide migration guide documentation
4. Monitor v1 usage analytics
5. Communicate sunset timeline to API consumers

## Success Metrics
- All 11 test cases passing
- Zero 404 errors from frontend API calls
- All responses include version header
- Backward compatibility verified for all legacy endpoints
