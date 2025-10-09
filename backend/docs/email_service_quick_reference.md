# Email Service Quick Reference

## Overview
Multi-backend email service supporting Console, File, and SMTP delivery with professional templates.

## Quick Start

### Import
```python
from app.services.email_service import (
    send_password_reset_email,
    send_welcome_email,
    EmailService,
    ConsoleEmailBackend,
    FileEmailBackend,
    SMTPEmailBackend
)
```

### Send Password Reset Email
```python
# Simple usage
await send_password_reset_email(
    to_email="user@example.com",
    reset_token="jwt_token_here",
    user_name="John Doe"  # Optional
)
```

### Send Welcome Email
```python
await send_welcome_email(
    to_email="newuser@example.com",
    user_name="Jane Smith"
)
```

### Custom Email
```python
from app.services.email_service import email_service

await email_service.send_email(
    to_email="recipient@example.com",
    subject="Your Subject",
    html_content="<p>HTML content</p>",
    text_content="Plain text fallback"  # Optional
)
```

## Environment Configuration

### Development (Console Backend)
```bash
ENVIRONMENT=development
# Emails print to console
```

### Testing (File Backend)
```bash
ENVIRONMENT=testing
# Emails saved to email_output/*.txt
```

### Production (SMTP Backend)
```bash
ENVIRONMENT=production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_FROM="OpenLearn <noreply@openlearn.co>"
```

## Backend Usage

### Console Backend (Development)
```python
backend = ConsoleEmailBackend()
service = EmailService(backend=backend)
```
**Output**: Prints to terminal with formatted display

### File Backend (Testing)
```python
from pathlib import Path
backend = FileEmailBackend(output_dir=Path("email_logs"))
service = EmailService(backend=backend)
```
**Output**: Saves to `email_logs/email_YYYYMMDD_HHMMSS.txt`

### SMTP Backend (Production)
```python
backend = SMTPEmailBackend(
    host="smtp.gmail.com",
    port=587,
    username="sender@gmail.com",
    password="app_password",
    use_tls=True
)
service = EmailService(backend=backend)
```
**Output**: Sends via SMTP server

## Password Reset Email Template

### Features
- 🔐 Branded header with gradient
- 🔗 Clickable reset button
- ⚠️ Security warnings box
- ⏰ 1-hour expiration notice
- 📱 Mobile-friendly responsive design
- 📝 Plain text fallback

### Security Warnings Included
1. Link expires in 1 hour
2. Only most recent link is valid
3. Ignore if you didn't request reset
4. Password won't change without clicking link

### Customization
```python
# Frontend URL configuration
# TODO: Update in email_service.py line 258
reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
```

## Welcome Email Template

### Features
- 🇨🇴 Bilingual greeting (Spanish/English)
- 🎯 Feature highlights
- 🔗 Dashboard link
- 👋 Personalized welcome

## Testing

### Run All Tests
```bash
cd backend
pytest tests/test_email_service.py -v
```

### Test Specific Backend
```bash
pytest tests/test_email_service.py::test_console_backend_single_recipient -v
pytest tests/test_email_service.py::test_file_backend_creates_email_file -v
pytest tests/test_email_service.py::test_smtp_backend_successful_send -v
```

### Test Password Reset Template
```bash
pytest tests/test_email_service.py -k "password_reset" -v
```

## Common Issues

### Issue: SMTP Authentication Failed
**Solution**:
1. Enable "Less secure app access" (Gmail)
2. Or use App Password (recommended)
3. Verify SMTP credentials

### Issue: Emails Not Sending
**Solution**:
1. Check environment configuration
2. Verify backend selection logic
3. Check logs for errors
4. Test with Console backend first

### Issue: Email Marked as Spam
**Solution**:
1. Configure SPF record
2. Enable DKIM signing
3. Add DMARC policy
4. Use authenticated SMTP

## Email Limits

### Gmail SMTP
- 500 emails/day (free)
- 2,000 emails/day (Google Workspace)
- 100 recipients per email

### SendGrid
- 100 emails/day (free)
- Unlimited (paid plans)

### AWS SES
- 200 emails/day (free tier)
- Pay-as-you-go beyond

## Performance Tips

1. **Use async**: All functions are async for non-blocking execution
2. **Batch sends**: Use `asyncio.gather()` for multiple emails
3. **Connection pooling**: Reuse SMTP connections (future enhancement)
4. **Rate limiting**: Respect SMTP provider limits

## Security Best Practices

1. **Never log email content**: May contain sensitive data
2. **Use environment variables**: Never hardcode credentials
3. **Validate email addresses**: Prevent injection attacks
4. **Use TLS**: Always encrypt SMTP connections
5. **Token expiration**: Short-lived reset tokens (1 hour)

## File Locations

| File | Purpose |
|------|---------|
| `app/services/email_service.py` | Main service implementation |
| `tests/test_email_service.py` | Comprehensive test suite |
| `docs/email_service_test_report.md` | Detailed test analysis |
| `app/config/settings.py` | Email configuration |

## API Reference

### EmailService

#### `send_email()`
```python
async def send_email(
    to_email: str | List[str],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None
) -> bool
```

#### `send_password_reset_email()`
```python
async def send_password_reset_email(
    to_email: str,
    reset_token: str,
    user_name: Optional[str] = None
) -> bool
```

#### `send_welcome_email()`
```python
async def send_welcome_email(
    to_email: str,
    user_name: str
) -> bool
```

## Return Values

All email functions return:
- `True`: Email sent successfully
- `False`: Email failed to send (check logs)

## Logging

Email operations log to:
- **Logger**: `app.services.email_service`
- **Level**: INFO (success), ERROR (failures)
- **Format**: Includes recipient and subject

Example logs:
```
INFO: Console email sent to ['user@example.com']: Reset Your Password
ERROR: Failed to send email via SMTP: Connection timeout
```

## Future Enhancements

- [ ] Email validation
- [ ] Retry logic with exponential backoff
- [ ] Jinja2 template engine
- [ ] Email tracking (open rates, clicks)
- [ ] Bounce handling
- [ ] Celery queue integration
- [ ] A/B testing support
- [ ] Unsubscribe management
- [ ] Multi-language templates

## Support

For issues or questions:
1. Check test suite for examples
2. Review detailed test report
3. Check service logs
4. Verify configuration

## License

Part of OpenLearn Colombia platform
© 2025 OpenLearn. All rights reserved.
