"""
Email Service for sending notifications and transactional emails.

Supports multiple backends:
- SMTP (Gmail, SendGrid, AWS SES)
- Console (Development - prints to console)
- File (Testing - saves to file)
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class EmailBackend:
    """Base email backend class"""

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email - must be implemented by subclasses"""
        raise NotImplementedError


class ConsoleEmailBackend(EmailBackend):
    """Email backend that prints to console (development)"""

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Print email to console"""
        recipients = to_email if isinstance(to_email, list) else [to_email]

        print("\n" + "=" * 80)
        print("📧 EMAIL (Console Backend)")
        print("=" * 80)
        print(f"From: {from_email or 'OpenLearn <noreply@openlearn.co>'}")
        print(f"To: {', '.join(recipients)}")
        print(f"Subject: {subject}")
        print("-" * 80)
        print(text_content or html_content)
        print("=" * 80 + "\n")

        logger.info(f"Console email sent to {recipients}: {subject}")
        return True


class FileEmailBackend(EmailBackend):
    """Email backend that saves to file (testing)"""

    def __init__(self, output_dir: Path = Path("email_output")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Save email to file"""
        recipients = to_email if isinstance(to_email, list) else [to_email]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"email_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"From: {from_email or 'OpenLearn <noreply@openlearn.co>'}\n")
            f.write(f"To: {', '.join(recipients)}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write("\n" + "-" * 80 + "\n\n")
            f.write(text_content or html_content)

        logger.info(f"File email saved to {filename}: {subject}")
        return True


class SMTPEmailBackend(EmailBackend):
    """SMTP email backend (production)"""

    def __init__(
        self,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email via SMTP"""
        try:
            recipients = to_email if isinstance(to_email, list) else [to_email]
            sender = from_email or settings.ALERT_EMAIL_FROM or "OpenLearn <noreply@openlearn.co>"

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_smtp,
                msg,
                sender,
                recipients
            )

            logger.info(f"SMTP email sent to {recipients}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False

    def _send_smtp(self, msg: MIMEMultipart, sender: str, recipients: List[str]):
        """Send email synchronously (called in executor)"""
        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(sender, recipients, msg.as_string())


class EmailService:
    """Main email service with template support"""

    def __init__(self, backend: Optional[EmailBackend] = None):
        """
        Initialize email service with specified backend.

        If no backend provided, auto-selects based on environment:
        - Production: SMTP (if configured)
        - Development: Console
        - Testing: File
        """
        if backend:
            self.backend = backend
        else:
            self.backend = self._get_default_backend()

    def _get_default_backend(self) -> EmailBackend:
        """Get default backend based on environment and configuration"""
        # Production with SMTP configured
        if settings.ENVIRONMENT == "production" and settings.SMTP_HOST:
            return SMTPEmailBackend(
                host=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_PORT in [587, 465]
            )

        # Testing environment
        if settings.ENVIRONMENT == "testing":
            return FileEmailBackend()

        # Default: Console (development)
        return ConsoleEmailBackend()

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send email using configured backend.

        Args:
            to_email: Recipient email address or list of addresses
            subject: Email subject line
            html_content: HTML email body
            text_content: Plain text email body (optional, fallback)
            from_email: Sender email address (optional, uses default)

        Returns:
            True if email sent successfully, False otherwise
        """
        return await self.backend.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email=from_email
        )

    # ========================================================================
    # Template-based Email Methods
    # ========================================================================

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email with reset link.

        Args:
            to_email: User's email address
            reset_token: Password reset JWT token
            user_name: User's display name (optional)

        Returns:
            True if email sent successfully
        """
        # TODO: Replace with actual frontend URL from settings
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"

        greeting = f"Hello {user_name}" if user_name else "Hello"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
                           color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ background: #f59e0b; color: white; padding: 12px 30px;
                          text-decoration: none; border-radius: 6px; display: inline-block;
                          margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
                .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b;
                           padding: 12px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 OpenLearn Colombia</h1>
                    <p>Password Reset Request</p>
                </div>
                <div class="content">
                    <p>{greeting},</p>
                    <p>We received a request to reset the password for your OpenLearn Colombia account.</p>
                    <p>Click the button below to reset your password:</p>
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666; font-size: 14px;">{reset_url}</p>
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul style="margin: 8px 0;">
                            <li>This link expires in 1 hour</li>
                            <li>Only the most recent reset link is valid</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your password will not change unless you click the link above</li>
                        </ul>
                    </div>
                    <p>If you're having trouble clicking the button, copy and paste the URL into your web browser.</p>
                    <p>Best regards,<br>The OpenLearn Colombia Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 OpenLearn Colombia. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        OpenLearn Colombia - Password Reset Request

        {greeting},

        We received a request to reset the password for your OpenLearn Colombia account.

        To reset your password, visit this link:
        {reset_url}

        SECURITY NOTICE:
        - This link expires in 1 hour
        - Only the most recent reset link is valid
        - If you didn't request this reset, please ignore this email
        - Your password will not change unless you click the link above

        Best regards,
        The OpenLearn Colombia Team

        ---
        © 2025 OpenLearn Colombia. All rights reserved.
        This is an automated message, please do not reply to this email.
        """

        return await self.send_email(
            to_email=to_email,
            subject="Reset Your Password - OpenLearn Colombia",
            html_content=html_content,
            text_content=text_content
        )

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> bool:
        """Send welcome email to new users"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f59e0b;">¡Bienvenido a OpenLearn Colombia! 🇨🇴</h1>
                <p>Hello {user_name},</p>
                <p>Thank you for joining OpenLearn Colombia, your gateway to understanding Colombia through data and language learning.</p>
                <h2>What's Next?</h2>
                <ul>
                    <li>📰 Explore news from 15+ Colombian media sources</li>
                    <li>📊 Analyze data from 7+ government APIs</li>
                    <li>📚 Learn Spanish with context-aware vocabulary extraction</li>
                    <li>🎯 Track your learning progress</li>
                </ul>
                <p>Ready to get started? <a href="http://localhost:3000/dashboard" style="color: #f59e0b;">Go to your dashboard</a></p>
                <p>Best regards,<br>The OpenLearn Team</p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to_email=to_email,
            subject="Welcome to OpenLearn Colombia! 🇨🇴",
            html_content=html_content
        )


# Global email service instance
email_service = EmailService()


# ============================================================================
# Convenience Functions
# ============================================================================

async def send_password_reset_email(to_email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
    """Convenience function to send password reset email"""
    return await email_service.send_password_reset_email(to_email, reset_token, user_name)


async def send_welcome_email(to_email: str, user_name: str) -> bool:
    """Convenience function to send welcome email"""
    return await email_service.send_welcome_email(to_email, user_name)
