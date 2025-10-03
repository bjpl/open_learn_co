"""
Email Notifier
Sends email notifications using SMTP with HTML templates
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader
import logging

from app.services.notifiers.base_notifier import BaseNotifier
from app.services.notification_service import NotificationService
from app.database.models import User
from app.config.settings import settings


logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Email notification delivery via SMTP"""

    def __init__(self, db):
        super().__init__(db)
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.ALERT_EMAIL_FROM or "noreply@openlearn.co"
        self.from_name = "OpenLearn Colombia"

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent.parent.parent / "templates" / "emails"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

    async def send(
        self,
        user: User,
        subject: str,
        content: Dict[str, Any],
        template: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Send email to a single user"""

        # Check if email notifications are enabled for this user
        if not await self.should_send(user):
            logger.info(f"Email notifications disabled for user {user.id}")
            return False

        # Check rate limits
        service = NotificationService(self.db)
        prefs = await service.get_user_preferences(user.id)

        if prefs and not await self._check_email_rate_limit(user.id, prefs.max_emails_per_day):
            logger.warning(f"Email rate limit exceeded for user {user.id}")
            return False

        try:
            # Render email content
            if template:
                html_content = await self._render_template(template, content, user)
                text_content = await self._render_plain_text(content)
            else:
                html_content = content.get("html", "")
                text_content = content.get("text", "")

            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = user.email

            # Attach plain text and HTML versions
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            if html_content:
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # Send email
            if self.smtp_host and self.smtp_user:
                await self._send_smtp(msg)
                logger.info(f"Email sent to {user.email}: {subject}")

                # Log successful send
                await service.log_email(
                    user_id=user.id,
                    email_type=template or "custom",
                    recipient=user.email,
                    subject=subject,
                    sent=True,
                    metadata=content
                )

                return True
            else:
                logger.warning("SMTP not configured, email not sent")

                # Log failed send
                await service.log_email(
                    user_id=user.id,
                    email_type=template or "custom",
                    recipient=user.email,
                    subject=subject,
                    sent=False,
                    error_message="SMTP not configured"
                )

                return False

        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")

            # Log error
            service = NotificationService(self.db)
            await service.log_email(
                user_id=user.id,
                email_type=template or "custom",
                recipient=user.email,
                subject=subject,
                sent=False,
                error_message=str(e)
            )

            return False

    async def send_bulk(
        self,
        users: List[User],
        subject: str,
        content: Dict[str, Any],
        template: Optional[str] = None,
        **kwargs
    ) -> Dict[int, bool]:
        """Send email to multiple users"""

        results = {}

        # Send in batches of 100 to avoid overwhelming SMTP server
        batch_size = 100
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]

            for user in batch:
                results[user.id] = await self.send(user, subject, content, template, **kwargs)

        return results

    async def should_send(self, user: User) -> bool:
        """Check if email should be sent to this user"""

        service = NotificationService(self.db)
        prefs = await service.get_user_preferences(user.id)

        # Check if email alerts are enabled
        if prefs and not prefs.email_alerts_enabled:
            return False

        # Check quiet hours (if implemented)
        # if await service._check_quiet_hours(user.id):
        #     return False

        return True

    async def _render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        user: User
    ) -> str:
        """Render Jinja2 email template"""

        # Add default context
        full_context = {
            "user_name": user.full_name or user.username,
            "user_email": user.email,
            "unsubscribe_url": f"{settings.CORS_ORIGINS[0]}/settings/notifications",
            "settings_url": f"{settings.CORS_ORIGINS[0]}/settings",
            **context
        }

        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            return template.render(**full_context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return ""

    async def _render_plain_text(self, content: Dict[str, Any]) -> str:
        """Generate plain text version from content"""

        # Simple plain text version
        text_parts = []

        if "greeting" in content:
            text_parts.append(content["greeting"])

        if "message" in content:
            text_parts.append(content["message"])

        if "action_text" in content and "action_url" in content:
            text_parts.append(f"{content['action_text']}: {content['action_url']}")

        return "\n\n".join(text_parts)

    async def _send_smtp(self, msg: MIMEMultipart):
        """Send email via SMTP"""

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    async def _check_email_rate_limit(self, user_id: int, max_per_day: int) -> bool:
        """Check if user has exceeded daily email limit"""

        from datetime import datetime, timedelta
        from sqlalchemy import select, func, and_
        from app.database.notification_models import EmailLog

        # Count emails sent in last 24 hours
        one_day_ago = datetime.utcnow() - timedelta(days=1)

        query = select(func.count()).where(
            and_(
                EmailLog.user_id == user_id,
                EmailLog.sent == True,
                EmailLog.created_at >= one_day_ago
            )
        )

        result = await self.db.execute(query)
        count = result.scalar()

        return count < max_per_day
