"""
Timezone utilities for handling user timezones and scheduling.

Provides timezone-aware datetime operations for notifications,
scheduling, and user activity tracking.
"""

from datetime import datetime, time, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, available_timezones
import logging

logger = logging.getLogger(__name__)


# Common timezones for Colombia and global users
COLOMBIA_TIMEZONE = "America/Bogota"
DEFAULT_TIMEZONE = "UTC"

# Valid timezone choices (subset of most common)
COMMON_TIMEZONES = [
    "America/Bogota",      # Colombia
    "America/New_York",    # US Eastern
    "America/Chicago",     # US Central
    "America/Denver",      # US Mountain
    "America/Los_Angeles", # US Pacific
    "Europe/London",       # UK
    "Europe/Paris",        # Central Europe
    "Europe/Madrid",       # Spain
    "Asia/Tokyo",          # Japan
    "Asia/Shanghai",       # China
    "Australia/Sydney",    # Australia
    "UTC",                 # Coordinated Universal Time
]


def validate_timezone(timezone_str: str) -> bool:
    """
    Validate if a timezone string is valid.

    Args:
        timezone_str: Timezone identifier (e.g., 'America/Bogota')

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_timezone('America/Bogota')
        True
        >>> validate_timezone('Invalid/Timezone')
        False
    """
    try:
        ZoneInfo(timezone_str)
        return True
    except Exception:
        return False


def get_user_timezone(user_timezone: Optional[str]) -> ZoneInfo:
    """
    Get ZoneInfo object for user's timezone, with fallback to default.

    Args:
        user_timezone: User's timezone string (can be None)

    Returns:
        ZoneInfo object for the timezone

    Example:
        >>> tz = get_user_timezone('America/Bogota')
        >>> tz.key
        'America/Bogota'
    """
    if user_timezone and validate_timezone(user_timezone):
        return ZoneInfo(user_timezone)
    return ZoneInfo(DEFAULT_TIMEZONE)


def utc_to_user_time(
    utc_datetime: datetime,
    user_timezone: Optional[str] = None
) -> datetime:
    """
    Convert UTC datetime to user's local time.

    Args:
        utc_datetime: Datetime in UTC
        user_timezone: User's timezone string (optional)

    Returns:
        Datetime converted to user's timezone

    Example:
        >>> utc_dt = datetime(2025, 10, 8, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        >>> local_dt = utc_to_user_time(utc_dt, 'America/Bogota')
        >>> local_dt.hour
        7  # Colombia is UTC-5
    """
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo('UTC'))

    user_tz = get_user_timezone(user_timezone)
    return utc_datetime.astimezone(user_tz)


def user_to_utc_time(
    local_datetime: datetime,
    user_timezone: Optional[str] = None
) -> datetime:
    """
    Convert user's local time to UTC.

    Args:
        local_datetime: Datetime in user's local timezone
        user_timezone: User's timezone string (optional)

    Returns:
        Datetime converted to UTC

    Example:
        >>> local_dt = datetime(2025, 10, 8, 7, 0, 0)
        >>> utc_dt = user_to_utc_time(local_dt, 'America/Bogota')
        >>> utc_dt.hour
        12  # Colombia is UTC-5, so 7am becomes 12pm UTC
    """
    user_tz = get_user_timezone(user_timezone)

    if local_datetime.tzinfo is None:
        local_datetime = local_datetime.replace(tzinfo=user_tz)

    return local_datetime.astimezone(ZoneInfo('UTC'))


def get_user_current_time(user_timezone: Optional[str] = None) -> datetime:
    """
    Get current time in user's timezone.

    Args:
        user_timezone: User's timezone string (optional)

    Returns:
        Current datetime in user's timezone

    Example:
        >>> now = get_user_current_time('America/Bogota')
        >>> now.tzinfo.key
        'America/Bogota'
    """
    utc_now = datetime.now(ZoneInfo('UTC'))
    return utc_to_user_time(utc_now, user_timezone)


def is_time_in_range(
    current_time: datetime,
    start_time: time,
    end_time: time
) -> bool:
    """
    Check if current time falls within a time range.

    Handles ranges that cross midnight (e.g., 22:00 to 06:00).

    Args:
        current_time: Current datetime
        start_time: Range start time
        end_time: Range end time

    Returns:
        True if current time is in range

    Example:
        >>> now = datetime(2025, 10, 8, 23, 0, 0)  # 11pm
        >>> start = time(22, 0)  # 10pm
        >>> end = time(6, 0)  # 6am
        >>> is_time_in_range(now, start, end)
        True  # 11pm is between 10pm and 6am
    """
    current_time_only = current_time.time()

    # If range doesn't cross midnight
    if start_time <= end_time:
        return start_time <= current_time_only <= end_time

    # If range crosses midnight (e.g., 22:00 to 06:00)
    return current_time_only >= start_time or current_time_only <= end_time


def is_in_quiet_hours(
    quiet_start: Optional[time],
    quiet_end: Optional[time],
    user_timezone: Optional[str] = None
) -> bool:
    """
    Check if current time is within user's quiet hours.

    Args:
        quiet_start: Quiet hours start time
        quiet_end: Quiet hours end time
        user_timezone: User's timezone string

    Returns:
        True if currently in quiet hours, False otherwise

    Example:
        >>> from datetime import time
        >>> is_in_quiet_hours(time(22, 0), time(6, 0), 'America/Bogota')
        # Returns True if current time in Colombia is between 10pm and 6am
    """
    if not quiet_start or not quiet_end:
        return False

    user_now = get_user_current_time(user_timezone)
    return is_time_in_range(user_now, quiet_start, quiet_end)


def calculate_next_delivery_time(
    target_hour: int,
    target_minute: int = 0,
    user_timezone: Optional[str] = None
) -> datetime:
    """
    Calculate next delivery time in user's timezone, converted to UTC.

    Used for scheduling daily digests and reminders.

    Args:
        target_hour: Target hour (0-23) in user's local time
        target_minute: Target minute (0-59), defaults to 0
        user_timezone: User's timezone string

    Returns:
        Next delivery datetime in UTC

    Example:
        >>> # Schedule for 8am user's local time
        >>> next_time = calculate_next_delivery_time(8, 0, 'America/Bogota')
        >>> # Returns UTC datetime for next 8am Colombia time
    """
    user_now = get_user_current_time(user_timezone)

    # Create target time today
    target_today = user_now.replace(
        hour=target_hour,
        minute=target_minute,
        second=0,
        microsecond=0
    )

    # If target time already passed today, schedule for tomorrow
    if user_now >= target_today:
        target_today += timedelta(days=1)

    # Convert to UTC for storage
    return user_to_utc_time(target_today, user_timezone)


def get_timezone_offset_hours(user_timezone: Optional[str] = None) -> float:
    """
    Get timezone offset from UTC in hours.

    Args:
        user_timezone: User's timezone string

    Returns:
        Offset in hours (can be negative or positive)

    Example:
        >>> get_timezone_offset_hours('America/Bogota')
        -5.0  # Colombia is UTC-5
        >>> get_timezone_offset_hours('Asia/Tokyo')
        9.0  # Japan is UTC+9
    """
    user_tz = get_user_timezone(user_timezone)
    utc_now = datetime.now(ZoneInfo('UTC'))
    local_now = utc_now.astimezone(user_tz)

    offset = local_now.utcoffset()
    return offset.total_seconds() / 3600 if offset else 0.0


def get_start_of_day_utc(
    user_timezone: Optional[str] = None,
    days_ago: int = 0
) -> datetime:
    """
    Get start of day (midnight) in user's timezone, returned in UTC.

    Useful for querying records from "today" in user's perspective.

    Args:
        user_timezone: User's timezone string
        days_ago: Number of days in the past (0 = today, 1 = yesterday)

    Returns:
        Start of day in UTC

    Example:
        >>> start = get_start_of_day_utc('America/Bogota')
        >>> # Returns midnight Colombia time, converted to UTC
    """
    user_now = get_user_current_time(user_timezone)
    start_of_day = user_now.replace(hour=0, minute=0, second=0, microsecond=0)

    if days_ago > 0:
        start_of_day -= timedelta(days=days_ago)

    return user_to_utc_time(start_of_day, user_timezone)


def get_end_of_day_utc(
    user_timezone: Optional[str] = None,
    days_ago: int = 0
) -> datetime:
    """
    Get end of day (23:59:59) in user's timezone, returned in UTC.

    Args:
        user_timezone: User's timezone string
        days_ago: Number of days in the past (0 = today, 1 = yesterday)

    Returns:
        End of day in UTC

    Example:
        >>> end = get_end_of_day_utc('America/Bogota')
        >>> # Returns 23:59:59 Colombia time, converted to UTC
    """
    user_now = get_user_current_time(user_timezone)
    end_of_day = user_now.replace(hour=23, minute=59, second=59, microsecond=999999)

    if days_ago > 0:
        end_of_day -= timedelta(days=days_ago)

    return user_to_utc_time(end_of_day, user_timezone)


def format_timezone_friendly(
    dt: datetime,
    user_timezone: Optional[str] = None,
    format_str: str = "%B %d, %Y at %I:%M %p %Z"
) -> str:
    """
    Format datetime in user-friendly way with timezone.

    Args:
        dt: Datetime to format
        user_timezone: User's timezone string
        format_str: strftime format string

    Returns:
        Formatted datetime string

    Example:
        >>> dt = datetime(2025, 10, 8, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        >>> format_timezone_friendly(dt, 'America/Bogota')
        'October 08, 2025 at 07:00 AM -05'
    """
    local_dt = utc_to_user_time(dt, user_timezone)
    return local_dt.strftime(format_str)


def get_business_hours_utc(
    business_start: time = time(9, 0),
    business_end: time = time(17, 0),
    user_timezone: Optional[str] = None
) -> Tuple[datetime, datetime]:
    """
    Get today's business hours in UTC.

    Args:
        business_start: Business hours start time
        business_end: Business hours end time
        user_timezone: User's timezone string

    Returns:
        Tuple of (start_utc, end_utc)

    Example:
        >>> start, end = get_business_hours_utc(time(9,0), time(17,0), 'America/Bogota')
        >>> # Returns 9am-5pm Colombia time converted to UTC range
    """
    user_now = get_user_current_time(user_timezone)

    start_local = user_now.replace(
        hour=business_start.hour,
        minute=business_start.minute,
        second=0,
        microsecond=0
    )

    end_local = user_now.replace(
        hour=business_end.hour,
        minute=business_end.minute,
        second=0,
        microsecond=0
    )

    return (
        user_to_utc_time(start_local, user_timezone),
        user_to_utc_time(end_local, user_timezone)
    )


# Timezone display helpers

def get_common_timezones_list() -> list[dict]:
    """
    Get list of common timezones for UI selection.

    Returns:
        List of dicts with timezone info for dropdown/select UI

    Example:
        >>> timezones = get_common_timezones_list()
        >>> timezones[0]
        {'value': 'America/Bogota', 'label': 'Colombia (America/Bogota)', 'offset': '-05:00'}
    """
    result = []
    utc_now = datetime.now(ZoneInfo('UTC'))

    for tz_name in COMMON_TIMEZONES:
        try:
            tz = ZoneInfo(tz_name)
            local_time = utc_now.astimezone(tz)
            offset = local_time.strftime('%z')
            offset_formatted = f"{offset[:3]}:{offset[3:]}"

            # Create friendly label
            parts = tz_name.split('/')
            region = parts[0] if len(parts) > 1 else ""
            city = parts[-1].replace('_', ' ')

            result.append({
                'value': tz_name,
                'label': f"{city} ({tz_name})",
                'offset': offset_formatted,
                'region': region
            })
        except Exception as e:
            logger.warning(f"Could not process timezone {tz_name}: {e}")

    return result
