"""
Alerting Infrastructure

This module provides:
- Alert rule definitions
- Notification channels (Slack, Email)
- Alert severity and routing
- Alert deduplication
"""

import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from enum import Enum

import aiohttp
from pydantic import BaseModel

from app.core.logging_config import get_logger
from app.config.settings import settings


logger = get_logger(__name__)


# ============================================================================
# Alert Models
# ============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    FIRING = "firing"
    RESOLVED = "resolved"


class Alert(BaseModel):
    """Alert model"""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.FIRING
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    timestamp: datetime = datetime.utcnow()
    resolved_at: Optional[datetime] = None


# ============================================================================
# Alert Rules
# ============================================================================

class AlertRule(BaseModel):
    """Alert rule definition"""
    rule_id: str
    name: str
    condition: str
    severity: AlertSeverity
    threshold: float
    duration: int  # seconds
    notification_channels: List[str]


# Predefined alert rules
ALERT_RULES = [
    AlertRule(
        rule_id="high_error_rate",
        name="High Error Rate",
        condition="error_rate > threshold",
        severity=AlertSeverity.ERROR,
        threshold=0.05,  # 5%
        duration=300,  # 5 minutes
        notification_channels=["slack", "email"]
    ),
    AlertRule(
        rule_id="slow_response_time",
        name="Slow Response Time",
        condition="p95_response_time > threshold",
        severity=AlertSeverity.WARNING,
        threshold=2000,  # 2 seconds
        duration=600,  # 10 minutes
        notification_channels=["slack"]
    ),
    AlertRule(
        rule_id="database_connection_failure",
        name="Database Connection Failure",
        condition="database_unavailable",
        severity=AlertSeverity.CRITICAL,
        threshold=1,
        duration=60,  # 1 minute
        notification_channels=["slack", "email"]
    ),
    AlertRule(
        rule_id="high_memory_usage",
        name="High Memory Usage",
        condition="memory_usage_percent > threshold",
        severity=AlertSeverity.WARNING,
        threshold=85,  # 85%
        duration=600,  # 10 minutes
        notification_channels=["slack"]
    ),
    AlertRule(
        rule_id="scraper_failure_rate",
        name="Scraper Failure Rate",
        condition="scraper_failure_rate > threshold",
        severity=AlertSeverity.ERROR,
        threshold=0.3,  # 30%
        duration=300,  # 5 minutes
        notification_channels=["slack", "email"]
    ),
]


# ============================================================================
# Notification Channels
# ============================================================================

class NotificationChannel:
    """Base notification channel"""

    async def send(self, alert: Alert) -> bool:
        """Send alert notification"""
        raise NotImplementedError


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""

    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel

    async def send(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        # Map severity to color
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff6600",
            AlertSeverity.CRITICAL: "#ff0000",
        }

        # Build Slack message
        message = {
            "channel": self.channel,
            "username": "OpenLearn Monitor",
            "icon_emoji": ":rotating_light:",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#808080"),
                    "title": f"{alert.severity.upper()}: {alert.title}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": alert.status.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.isoformat(),
                            "short": False
                        },
                    ],
                    "footer": "OpenLearn Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }

        # Add labels as fields
        for key, value in alert.labels.items():
            message["attachments"][0]["fields"].append({
                "title": key,
                "value": value,
                "short": True
            })

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    if response.status == 200:
                        logger.info(
                            "alert_sent_to_slack",
                            alert_id=alert.alert_id,
                            severity=alert.severity
                        )
                        return True
                    else:
                        logger.error(
                            "slack_notification_failed",
                            status=response.status,
                            response=await response.text()
                        )
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: List[str]
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails

    async def send(self, alert: Alert) -> bool:
        """Send alert via email"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("Email configuration incomplete")
            return False

        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        # Plain text version
        text = f"""
{alert.title}

Severity: {alert.severity.upper()}
Status: {alert.status.upper()}
Time: {alert.timestamp.isoformat()}

{alert.message}

Labels:
{chr(10).join(f'  {k}: {v}' for k, v in alert.labels.items())}

---
OpenLearn Monitoring System
        """

        # HTML version
        html = f"""
<html>
  <body>
    <h2 style="color: {'red' if alert.severity == AlertSeverity.CRITICAL else 'orange' if alert.severity == AlertSeverity.ERROR else 'goldenrod'};">
      {alert.title}
    </h2>

    <p><strong>Severity:</strong> {alert.severity.upper()}</p>
    <p><strong>Status:</strong> {alert.status.upper()}</p>
    <p><strong>Time:</strong> {alert.timestamp.isoformat()}</p>

    <p>{alert.message}</p>

    <h3>Labels:</h3>
    <ul>
      {''.join(f'<li><strong>{k}:</strong> {v}</li>' for k, v in alert.labels.items())}
    </ul>

    <hr>
    <p style="color: gray; font-size: 0.8em;">OpenLearn Monitoring System</p>
  </body>
</html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_email_sync,
                msg
            )

            logger.info(
                "alert_sent_via_email",
                alert_id=alert.alert_id,
                severity=alert.severity,
                recipients=len(self.to_emails)
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _send_email_sync(self, msg: MIMEMultipart):
        """Send email synchronously"""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)


# ============================================================================
# Alert Manager
# ============================================================================

class AlertManager:
    """
    Alert manager for routing and deduplication
    """

    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Initialize channels
        self._initialize_channels()

    def _initialize_channels(self):
        """Initialize notification channels"""
        # Slack
        if settings.SLACK_WEBHOOK_URL:
            self.channels["slack"] = SlackNotificationChannel(
                webhook_url=settings.SLACK_WEBHOOK_URL,
                channel=settings.SLACK_CHANNEL
            )

        # Email
        if all([
            settings.SMTP_HOST,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.ALERT_EMAIL_FROM,
            settings.ALERT_EMAIL_TO
        ]):
            self.channels["email"] = EmailNotificationChannel(
                smtp_host=settings.SMTP_HOST,
                smtp_port=settings.SMTP_PORT,
                smtp_user=settings.SMTP_USER,
                smtp_password=settings.SMTP_PASSWORD,
                from_email=settings.ALERT_EMAIL_FROM,
                to_emails=settings.ALERT_EMAIL_TO
            )

    async def fire_alert(
        self,
        alert: Alert,
        notification_channels: List[str] | None = None
    ):
        """
        Fire an alert

        Args:
            alert: Alert to fire
            notification_channels: Channels to send to (default: all)
        """
        # Check for duplicate
        if alert.alert_id in self.active_alerts:
            logger.debug(f"Alert {alert.alert_id} already active, skipping")
            return

        # Add to active alerts
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        logger.warning(
            "alert_fired",
            alert_id=alert.alert_id,
            title=alert.title,
            severity=alert.severity
        )

        # Send notifications
        channels_to_use = notification_channels or list(self.channels.keys())

        for channel_name in channels_to_use:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    await channel.send(alert)
                except Exception as e:
                    logger.error(f"Failed to send to {channel_name}: {e}")

    async def resolve_alert(self, alert_id: str):
        """
        Resolve an active alert

        Args:
            alert_id: Alert ID to resolve
        """
        if alert_id not in self.active_alerts:
            logger.warning(f"Alert {alert_id} not found in active alerts")
            return

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()

        # Remove from active alerts
        del self.active_alerts[alert_id]

        logger.info(
            "alert_resolved",
            alert_id=alert_id,
            duration_seconds=(alert.resolved_at - alert.timestamp).seconds
        )

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get recent alert history"""
        return self.alert_history[-limit:]


# Global alert manager instance
alert_manager = AlertManager()
