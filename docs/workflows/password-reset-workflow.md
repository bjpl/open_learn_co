# Password Reset Workflow Documentation

## Overview

Complete email-based password reset functionality for OpenLearn Colombia, allowing users to securely recover their accounts when they forget their passwords.

## Architecture

### Backend Components

**Endpoints:**
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-update` - Update password with token

**Security Features:**
- JWT-based reset tokens (1-hour expiration)
- Rate limiting: 3 requests per hour per email/IP
- Password strength validation (uppercase, lowercase, number, special char, 8+ chars)
- Refresh token revocation on password change
- No user enumeration (same response for existing/non-existing emails)

**Email Service:**
- Console backend (development) - prints to terminal
- File backend (testing) - saves to files
- SMTP backend (production) - real email delivery

### Frontend Components

**Pages:**
- `/forgot-password` - Request reset link
- `/reset-password?token=xxx` - Set new password

**Components:**
- `PasswordResetForm` - Dual-mode form (request/confirm)
- Password strength indicator
- Real-time validation

**Validation:**
- Zod schemas with password strength rules
- Confirm password matching
- Clear error messages

## User Flow

### Step 1: Request Password Reset

1. User visits `/forgot-password`
2. Enters email address
3. System:
   - Validates email format
   - Checks rate limit (3 per hour)
   - If user exists:
     - Generates JWT reset token (1-hour expiry)
     - Sends email with reset link
   - Returns success message (doesn't reveal if email exists)

**Email Content:**
```
Subject: Reset Your Password - OpenLearn Colombia

Hello [Name],

We received a request to reset your password.

[Reset Password Button] → /reset-password?token=xxx

Link expires in 1 hour.

If you didn't request this, ignore this email.
```

### Step 2: Reset Password

1. User clicks email link → `/reset-password?token=xxx`
2. Page extracts token from URL
3. User enters new password (with confirmation)
4. Password strength indicator shows strength
5. On submit:
   - Validates token (not expired, correct type)
   - Validates password strength
   - Updates password hash
   - Revokes all refresh tokens (security measure)
   - Redirects to login

### Step 3: Login with New Password

1. User visits `/login`
2. Enters email + new password
3. Successfully authenticates

## Configuration

### Environment Variables

**Backend (`backend/.env`):**
```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com          # SMTP server
SMTP_PORT=587                     # SMTP port (587 for TLS, 465 for SSL)
SMTP_USER=your-email@gmail.com    # SMTP username
SMTP_PASSWORD=your-app-password   # SMTP password (use app password for Gmail)
ALERT_EMAIL_FROM=noreply@openlearn.co  # From address

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:3000  # Development
# FRONTEND_URL=https://openlearn.co  # Production

# JWT Settings (already configured)
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development  # development, testing, production
```

**Frontend (`frontend/.env.local`):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Email Backend Selection

The email service automatically selects the backend:

- **Production** (ENVIRONMENT=production + SMTP configured) → SMTP
- **Testing** (ENVIRONMENT=testing) → File (saves to `email_output/`)
- **Development** (default) → Console (prints to terminal)

### Gmail Configuration (Development/Testing)

1. Enable 2-factor authentication on Gmail account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use app password in `SMTP_PASSWORD`

### Production Email Services

**Recommended providers:**
- **SendGrid**: Free tier (100 emails/day)
- **AWS SES**: Pay-as-you-go ($0.10 per 1000 emails)
- **Mailgun**: Free tier (5000 emails/month)
- **Postmark**: Free tier (100 emails/month)

## Rate Limiting

### Implementation

**Decorator-based rate limiting:**
```python
@router.post("/password-reset")
@rate_limit(max_requests=3, window_seconds=3600)  # 3 per hour
async def request_password_reset(...):
    ...
```

**Identifier:**
- Email address (if in request body)
- IP address (fallback)

**Storage:**
- In-memory (current implementation)
- Redis (recommended for production with multiple workers)

### Rate Limit Response

**Status Code:** `429 Too Many Requests`

**Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Maximum 3 requests per 1 hour(s).",
  "retry_after": 3456,
  "limit": 3,
  "window_seconds": 3600
}
```

**Headers:**
```
Retry-After: 3456
X-RateLimit-Limit: 3
X-RateLimit-Window: 3600
```

## Security Considerations

### ✅ Implemented

1. **No User Enumeration** - Same response for existing/non-existing emails
2. **Token Expiration** - 1-hour window reduces attack surface
3. **Password Strength** - Enforced: 8+ chars, upper, lower, number, special
4. **Rate Limiting** - Prevents brute force (3 per hour)
5. **Refresh Token Revocation** - Invalidates active sessions on password change
6. **HTTPS** - All password reset links use HTTPS in production
7. **Token Type Validation** - Only password_reset tokens accepted

### 🔄 Future Enhancements

1. **Database Token Storage** - Track used tokens, enable one-time use
2. **Account Lockout** - Lock account after X failed reset attempts
3. **Security Notifications** - Email user when password changed
4. **2FA Integration** - Require 2FA for high-value accounts
5. **Redis Rate Limiting** - For distributed systems
6. **IP Geolocation** - Warn about resets from new locations

## Testing

### Manual Testing

**Development:**
```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal, check console for email output
# Click the reset link from console output

# Start frontend
cd frontend
npm run dev

# Visit http://localhost:3000/forgot-password
```

**Test Flow:**
1. Register a user at `/register`
2. Request password reset at `/forgot-password`
3. Check backend console for email with reset link
4. Click reset link (or copy URL to browser)
5. Enter new password at `/reset-password?token=xxx`
6. Login with new password at `/login`

### Automated Testing

```bash
cd backend
pytest tests/api/test_password_reset.py -v
```

**Test Coverage:**
- ✅ Request reset with valid email
- ✅ Request reset with non-existent email (no enumeration)
- ✅ Request reset with invalid email format
- ✅ Rate limiting (3 per hour)
- ✅ Update password with valid token
- ✅ Update password with expired token
- ✅ Update password with invalid token
- ✅ Weak password rejection
- ✅ Login with new password
- ✅ Old password invalidation
- ✅ Regular token cannot reset password

## Success Criteria

### ✅ Functional Requirements

- [x] User can request password reset via email
- [x] Reset email delivered with secure token
- [x] Reset form validates password strength
- [x] Token expires after 1 hour
- [x] Rate limit: 3 requests per hour per email/IP
- [x] User can login with new password
- [x] Old password no longer works

### ✅ Security Requirements

- [x] No user enumeration
- [x] JWT token validation
- [x] Password strength enforcement
- [x] Rate limiting protection
- [x] Refresh token revocation
- [x] HTTPS-only reset links (production)

### ✅ UX Requirements

- [x] Clear instructions in email
- [x] Password strength indicator
- [x] Real-time validation
- [x] Helpful error messages
- [x] Mobile-responsive design

## Troubleshooting

### Email not sending

**Check:**
1. `ENVIRONMENT` variable (console/file/production)
2. SMTP credentials in `.env`
3. Gmail app password (not account password)
4. Backend console for email output (development)
5. `email_output/` directory (testing)

### Token invalid/expired

**Check:**
1. Token was used within 1 hour of generation
2. Token copied completely from email
3. No extra spaces in token
4. `JWT_SECRET_KEY` hasn't changed

### Rate limiting triggered

**Wait:** 1 hour from first request, or clear in-memory storage by restarting backend

### Password validation failing

**Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*(),.?":{}|<>)

## API Reference

### Request Password Reset

```http
POST /api/v1/auth/password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "If the email exists, a reset link has been sent"
}
```

**Rate Limited (429):**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Maximum 3 requests per 1 hour(s).",
  "retry_after": 3456
}
```

### Update Password

```http
POST /api/v1/auth/password-update
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully"
}
```

**Invalid Token (400):**
```json
{
  "detail": "Invalid or expired reset token"
}
```

## Monitoring & Metrics

### Key Metrics to Track

1. **Password Reset Request Rate** - Requests per hour/day
2. **Reset Completion Rate** - % of requests that complete
3. **Token Expiration Rate** - % of tokens that expire unused
4. **Rate Limit Triggers** - Frequency of rate limiting
5. **Email Delivery Rate** - % of emails successfully delivered
6. **Time to Complete** - Average time from request to completion

### Alerts

- High rate limit trigger frequency (possible attack)
- Low email delivery rate (SMTP issues)
- Spike in reset requests (possible credential stuffing)

## Migration Notes

**Database Migration:** NOT REQUIRED

The current implementation uses JWT tokens (stateless), so no database schema changes are needed. The existing `User` model already has all required fields.

**Future Enhancement:** If you want to add database-stored tokens for one-time use:

```python
# Migration: Add reset token fields
class User(Base):
    reset_token_hash: str = Column(String(255), nullable=True)
    reset_token_expires: datetime = Column(DateTime, nullable=True)
```

## Support & Resources

- **Documentation**: This file
- **Tests**: `backend/tests/api/test_password_reset.py`
- **Email Templates**: `backend/app/services/email_service.py`
- **Rate Limiter**: `backend/app/middleware/endpoint_rate_limiter.py`
- **Frontend Forms**: `frontend/src/components/auth/PasswordResetForm.tsx`

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Status:** ✅ Production Ready
