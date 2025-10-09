"""
Comprehensive tests for email service implementation.

Tests cover:
- All email backend types (Console, File, SMTP)
- Password reset email template validation
- Multi-backend pattern implementation
- Error handling and fallbacks
- Async email sending (non-blocking)
- Template content validation
"""

import asyncio
import os
import re
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import pytest
import tempfile
import shutil

# Import email service components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.email_service import (
    EmailBackend,
    ConsoleEmailBackend,
    FileEmailBackend,
    SMTPEmailBackend,
    EmailService,
    send_password_reset_email,
    send_welcome_email
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_email_dir():
    """Create temporary directory for file backend testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def console_backend():
    """Console email backend instance"""
    return ConsoleEmailBackend()


@pytest.fixture
def file_backend(temp_email_dir):
    """File email backend instance"""
    return FileEmailBackend(output_dir=temp_email_dir)


@pytest.fixture
def smtp_backend():
    """SMTP email backend instance (mocked)"""
    return SMTPEmailBackend(
        host="smtp.gmail.com",
        port=587,
        username="test@example.com",
        password="test_password",
        use_tls=True
    )


@pytest.fixture
def email_service_console():
    """Email service with console backend"""
    return EmailService(backend=ConsoleEmailBackend())


@pytest.fixture
def email_service_file(temp_email_dir):
    """Email service with file backend"""
    return EmailService(backend=FileEmailBackend(output_dir=temp_email_dir))


# ============================================================================
# Test 1: Console Backend Implementation
# ============================================================================

@pytest.mark.asyncio
async def test_console_backend_single_recipient(console_backend, capsys):
    """Test console backend prints email correctly for single recipient"""
    result = await console_backend.send_email(
        to_email="user@example.com",
        subject="Test Email",
        html_content="<p>Test content</p>",
        text_content="Test content"
    )

    assert result is True

    captured = capsys.readouterr()
    output = captured.out

    # Verify all required elements
    assert "=" * 80 in output
    assert "EMAIL (Console Backend)" in output
    assert "From:" in output
    assert "To: user@example.com" in output
    assert "Subject: Test Email" in output
    assert "Test content" in output


@pytest.mark.asyncio
async def test_console_backend_multiple_recipients(console_backend, capsys):
    """Test console backend handles multiple recipients"""
    recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

    result = await console_backend.send_email(
        to_email=recipients,
        subject="Multi-recipient Test",
        html_content="<p>Content</p>"
    )

    assert result is True

    captured = capsys.readouterr()
    output = captured.out

    # Verify all recipients listed
    for email in recipients:
        assert email in output


@pytest.mark.asyncio
async def test_console_backend_custom_from_email(console_backend, capsys):
    """Test console backend uses custom from email"""
    result = await console_backend.send_email(
        to_email="user@example.com",
        subject="Test",
        html_content="<p>Content</p>",
        from_email="custom@sender.com"
    )

    assert result is True

    captured = capsys.readouterr()
    output = captured.out

    assert "From: custom@sender.com" in output


# ============================================================================
# Test 2: File Backend Implementation
# ============================================================================

@pytest.mark.asyncio
async def test_file_backend_creates_email_file(file_backend, temp_email_dir):
    """Test file backend creates email file with correct content"""
    result = await file_backend.send_email(
        to_email="user@example.com",
        subject="Test Email",
        html_content="<p>Test content</p>",
        text_content="Test content"
    )

    assert result is True

    # Check file was created
    email_files = list(temp_email_dir.glob("email_*.txt"))
    assert len(email_files) == 1

    # Verify file content
    with open(email_files[0], 'r', encoding='utf-8') as f:
        content = f.read()

    assert "From:" in content
    assert "To: user@example.com" in content
    assert "Subject: Test Email" in content
    assert "Test content" in content


@pytest.mark.asyncio
async def test_file_backend_multiple_emails(file_backend, temp_email_dir):
    """Test file backend creates separate files for multiple emails"""
    # Send 3 emails
    for i in range(3):
        await file_backend.send_email(
            to_email=f"user{i}@example.com",
            subject=f"Email {i}",
            html_content=f"<p>Content {i}</p>"
        )
        # Delay to ensure unique timestamps (1 second granularity in filename)
        await asyncio.sleep(1.1)

    # Check 3 files created
    email_files = list(temp_email_dir.glob("email_*.txt"))
    assert len(email_files) == 3


@pytest.mark.asyncio
async def test_file_backend_directory_creation(temp_email_dir):
    """Test file backend creates output directory if it doesn't exist"""
    new_dir = temp_email_dir / "email_output"
    backend = FileEmailBackend(output_dir=new_dir)

    assert new_dir.exists()


# ============================================================================
# Test 3: SMTP Backend Implementation (Mocked)
# ============================================================================

@pytest.mark.asyncio
async def test_smtp_backend_successful_send(smtp_backend):
    """Test SMTP backend sends email successfully"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await smtp_backend.send_email(
            to_email="user@example.com",
            subject="Test Email",
            html_content="<p>Test content</p>",
            text_content="Test content"
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_smtp_backend_error_handling(smtp_backend):
    """Test SMTP backend handles errors gracefully"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = Exception("Connection failed")

        result = await smtp_backend.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Content</p>"
        )

        assert result is False


@pytest.mark.asyncio
async def test_smtp_backend_multiple_recipients(smtp_backend):
    """Test SMTP backend handles multiple recipients"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        recipients = ["user1@example.com", "user2@example.com"]
        result = await smtp_backend.send_email(
            to_email=recipients,
            subject="Test",
            html_content="<p>Content</p>"
        )

        assert result is True
        # Verify sendmail called with list of recipients
        call_args = mock_server.sendmail.call_args
        assert call_args[0][1] == recipients


# ============================================================================
# Test 4: Password Reset Email Template Validation
# ============================================================================

@pytest.mark.asyncio
async def test_password_reset_email_contains_reset_link(email_service_console):
    """Test password reset email includes reset link"""
    reset_token = "test_token_12345"

    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        await email_service_console.send_password_reset_email(
            to_email="user@example.com",
            reset_token=reset_token,
            user_name="Test User"
        )

        # Get the HTML content from the call
        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']

        # Verify reset link is present
        assert f"reset-password?token={reset_token}" in html_content


@pytest.mark.asyncio
async def test_password_reset_email_security_warnings(email_service_console):
    """Test password reset email contains all security warnings"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        await email_service_console.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token"
        )

        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']
        text_content = call_args.kwargs['text_content']

        # Check HTML content
        assert "Security Notice" in html_content or "⚠️" in html_content
        assert "1 hour" in html_content
        assert "didn't request" in html_content
        assert "most recent" in html_content

        # Check text content
        assert "SECURITY NOTICE" in text_content
        assert "1 hour" in text_content
        assert "didn't request" in text_content


@pytest.mark.asyncio
async def test_password_reset_email_expiration_notice(email_service_console):
    """Test password reset email mentions 1-hour expiration"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        await email_service_console.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token"
        )

        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']

        # Verify expiration is mentioned
        assert "expires in 1 hour" in html_content.lower()


@pytest.mark.asyncio
async def test_password_reset_email_professional_formatting(email_service_console):
    """Test password reset email has professional HTML formatting"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        await email_service_console.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token",
            user_name="Test User"
        )

        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']

        # Verify HTML structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html>" in html_content
        assert "<head>" in html_content
        assert "<style>" in html_content
        assert "<body>" in html_content

        # Verify styling elements
        assert "font-family" in html_content
        assert "color:" in html_content
        assert "padding:" in html_content

        # Verify branding
        assert "OpenLearn" in html_content


@pytest.mark.asyncio
async def test_password_reset_email_personalization(email_service_console):
    """Test password reset email personalizes greeting with user name"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        # Test with user name
        await email_service_console.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token",
            user_name="John Doe"
        )

        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']

        assert "Hello John Doe" in html_content


@pytest.mark.asyncio
async def test_password_reset_email_fallback_greeting(email_service_console):
    """Test password reset email uses generic greeting without name"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        # Test without user name
        await email_service_console.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token"
        )

        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']

        # Should have generic greeting
        assert "Hello," in html_content or "Hello" in html_content


# ============================================================================
# Test 5: Multi-Backend Pattern Verification
# ============================================================================

def test_email_service_accepts_custom_backend():
    """Test EmailService accepts custom backend"""
    custom_backend = ConsoleEmailBackend()
    service = EmailService(backend=custom_backend)

    assert service.backend is custom_backend


def test_email_service_default_backend_development():
    """Test EmailService defaults to Console backend in development"""
    with patch('app.services.email_service.settings') as mock_settings:
        mock_settings.ENVIRONMENT = "development"
        mock_settings.SMTP_HOST = None

        service = EmailService()

        assert isinstance(service.backend, ConsoleEmailBackend)


def test_email_service_default_backend_testing():
    """Test EmailService defaults to File backend in testing"""
    with patch('app.services.email_service.settings') as mock_settings:
        mock_settings.ENVIRONMENT = "testing"

        service = EmailService()

        assert isinstance(service.backend, FileEmailBackend)


def test_email_service_default_backend_production():
    """Test EmailService defaults to SMTP backend in production with config"""
    with patch('app.services.email_service.settings') as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password"

        service = EmailService()

        assert isinstance(service.backend, SMTPEmailBackend)


# ============================================================================
# Test 6: Error Handling and Fallbacks
# ============================================================================

@pytest.mark.asyncio
async def test_email_service_handles_backend_failure(email_service_console):
    """Test EmailService returns False on backend failure"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = False

        result = await email_service_console.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Content</p>"
        )

        assert result is False


@pytest.mark.asyncio
async def test_smtp_backend_no_credentials():
    """Test SMTP backend works without credentials (for relay servers)"""
    backend = SMTPEmailBackend(
        host="smtp.example.com",
        port=25,
        username=None,
        password=None,
        use_tls=False
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await backend.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Content</p>"
        )

        assert result is True
        mock_server.login.assert_not_called()


@pytest.mark.asyncio
async def test_email_service_invalid_email_format():
    """Test email service handles invalid email gracefully"""
    service = EmailService(backend=ConsoleEmailBackend())

    # Should not raise exception
    result = await service.send_email(
        to_email="invalid-email",
        subject="Test",
        html_content="<p>Content</p>"
    )

    # Backend should still return True (it doesn't validate)
    assert result is True


# ============================================================================
# Test 7: Async Email Sending (Non-blocking)
# ============================================================================

@pytest.mark.asyncio
async def test_smtp_backend_async_execution():
    """Test SMTP backend executes in thread pool (non-blocking)"""
    backend = SMTPEmailBackend(
        host="smtp.gmail.com",
        port=587,
        username="test@example.com",
        password="password"
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Record thread execution
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = None
            mock_loop.return_value.run_in_executor = mock_executor

            await backend.send_email(
                to_email="user@example.com",
                subject="Test",
                html_content="<p>Content</p>"
            )

            # Verify execution in thread pool
            mock_executor.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_email_sending():
    """Test multiple emails can be sent concurrently"""
    service = EmailService(backend=ConsoleEmailBackend())

    # Send 5 emails concurrently
    tasks = [
        service.send_email(
            to_email=f"user{i}@example.com",
            subject=f"Email {i}",
            html_content=f"<p>Content {i}</p>"
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    assert all(results)
    assert len(results) == 5


# ============================================================================
# Test 8: Convenience Functions
# ============================================================================

@pytest.mark.asyncio
async def test_convenience_function_password_reset():
    """Test global send_password_reset_email function"""
    with patch('app.services.email_service.email_service') as mock_service:
        mock_service.send_password_reset_email = AsyncMock(return_value=True)

        result = await send_password_reset_email(
            to_email="user@example.com",
            reset_token="token",
            user_name="Test User"
        )

        assert result is True
        mock_service.send_password_reset_email.assert_called_once()


@pytest.mark.asyncio
async def test_convenience_function_welcome_email():
    """Test global send_welcome_email function"""
    with patch('app.services.email_service.email_service') as mock_service:
        mock_service.send_welcome_email = AsyncMock(return_value=True)

        result = await send_welcome_email(
            to_email="user@example.com",
            user_name="Test User"
        )

        assert result is True
        mock_service.send_welcome_email.assert_called_once()


# ============================================================================
# Test 9: Welcome Email Validation
# ============================================================================

@pytest.mark.asyncio
async def test_welcome_email_content(email_service_console):
    """Test welcome email contains expected content"""
    with patch.object(email_service_console.backend, 'send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        await email_service_console.send_welcome_email(
            to_email="user@example.com",
            user_name="Test User"
        )

        call_args = mock_send.call_args
        html_content = call_args.kwargs['html_content']

        # Verify content elements
        assert "Bienvenido" in html_content or "Welcome" in html_content
        assert "Test User" in html_content
        assert "OpenLearn Colombia" in html_content
        assert "dashboard" in html_content.lower()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
