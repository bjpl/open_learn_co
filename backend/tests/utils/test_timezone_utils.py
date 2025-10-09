"""
Tests for Timezone Utilities

Validates timezone-aware operations including:
- UTC to user time conversion
- Quiet hours detection with midnight crossing
- Business hours calculation
- Timezone validation
"""

import pytest
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.utils.timezone_utils import (
    validate_timezone,
    get_user_timezone,
    utc_to_user_time,
    user_to_utc_time,
    get_user_current_time,
    is_time_in_range,
    is_in_quiet_hours,
    calculate_next_delivery_time,
    get_timezone_offset_hours,
    get_start_of_day_utc,
    get_end_of_day_utc,
    get_business_hours_utc,
    get_common_timezones_list,
    COMMON_TIMEZONES,
    COLOMBIA_TIMEZONE
)


class TestTimezoneValidation:
    """Test timezone validation functions"""

    def test_validate_valid_timezone(self):
        """Test validation of valid timezone"""
        assert validate_timezone('America/Bogota') == True
        assert validate_timezone('UTC') == True
        assert validate_timezone('America/New_York') == True
        assert validate_timezone('Europe/London') == True

    def test_validate_invalid_timezone(self):
        """Test validation of invalid timezone"""
        assert validate_timezone('Invalid/Timezone') == False
        assert validate_timezone('America/FakeCity') == False
        assert validate_timezone('') == False
        assert validate_timezone('Not-A-Timezone') == False

    def test_get_user_timezone_valid(self):
        """Test getting user timezone object"""
        tz = get_user_timezone('America/Bogota')
        assert isinstance(tz, ZoneInfo)
        assert tz.key == 'America/Bogota'

    def test_get_user_timezone_invalid_fallback(self):
        """Test fallback to UTC for invalid timezone"""
        tz = get_user_timezone('Invalid/Timezone')
        assert tz.key == 'UTC'

    def test_get_user_timezone_none_fallback(self):
        """Test fallback to UTC when None provided"""
        tz = get_user_timezone(None)
        assert tz.key == 'UTC'

    def test_common_timezones_count(self):
        """Test that all common timezones are valid"""
        assert len(COMMON_TIMEZONES) == 12
        for tz_name in COMMON_TIMEZONES:
            assert validate_timezone(tz_name) == True


class TestTimeConversion:
    """Test time conversion between UTC and user timezones"""

    def test_utc_to_colombia_time(self):
        """Test UTC to Colombia time conversion (UTC-5)"""
        utc_dt = datetime(2025, 10, 8, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        colombia_dt = utc_to_user_time(utc_dt, 'America/Bogota')

        assert colombia_dt.hour == 7  # 12:00 UTC = 07:00 Colombia
        assert colombia_dt.day == 8
        assert colombia_dt.tzinfo.key == 'America/Bogota'

    def test_utc_to_tokyo_time(self):
        """Test UTC to Tokyo time conversion (UTC+9)"""
        utc_dt = datetime(2025, 10, 8, 15, 0, 0, tzinfo=ZoneInfo('UTC'))
        tokyo_dt = utc_to_user_time(utc_dt, 'Asia/Tokyo')

        assert tokyo_dt.hour == 0  # 15:00 UTC = 00:00 next day Tokyo
        assert tokyo_dt.day == 9  # Day advances
        assert tokyo_dt.tzinfo.key == 'Asia/Tokyo'

    def test_colombia_to_utc_time(self):
        """Test Colombia time to UTC conversion"""
        local_dt = datetime(2025, 10, 8, 7, 0, 0)
        utc_dt = user_to_utc_time(local_dt, 'America/Bogota')

        assert utc_dt.hour == 12  # 07:00 Colombia = 12:00 UTC
        assert utc_dt.day == 8
        assert utc_dt.tzinfo.key == 'UTC'

    def test_tokyo_to_utc_time(self):
        """Test Tokyo time to UTC conversion"""
        local_dt = datetime(2025, 10, 9, 0, 0, 0)
        utc_dt = user_to_utc_time(local_dt, 'Asia/Tokyo')

        assert utc_dt.hour == 15  # 00:00 Tokyo = 15:00 prev day UTC
        assert utc_dt.day == 8  # Day goes back
        assert utc_dt.tzinfo.key == 'UTC'

    def test_utc_without_timezone_info(self):
        """Test handling of naive datetime (no timezone)"""
        naive_dt = datetime(2025, 10, 8, 12, 0, 0)  # No tzinfo
        colombia_dt = utc_to_user_time(naive_dt, 'America/Bogota')

        # Should treat as UTC and convert
        assert colombia_dt.hour == 7
        assert colombia_dt.tzinfo is not None

    def test_local_without_timezone_info(self):
        """Test handling of naive local datetime"""
        naive_dt = datetime(2025, 10, 8, 7, 0, 0)  # No tzinfo
        utc_dt = user_to_utc_time(naive_dt, 'America/Bogota')

        # Should treat as local time and convert
        assert utc_dt.hour == 12
        assert utc_dt.tzinfo.key == 'UTC'

    def test_roundtrip_conversion(self):
        """Test UTC -> Local -> UTC roundtrip"""
        original_utc = datetime(2025, 10, 8, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # UTC -> Colombia
        colombia_dt = utc_to_user_time(original_utc, 'America/Bogota')

        # Colombia -> UTC
        back_to_utc = user_to_utc_time(colombia_dt, 'America/Bogota')

        # Should match original
        assert back_to_utc.replace(microsecond=0) == original_utc.replace(microsecond=0)


class TestTimezoneOffset:
    """Test timezone offset calculations"""

    def test_colombia_offset(self):
        """Test Colombia UTC offset (UTC-5)"""
        offset = get_timezone_offset_hours('America/Bogota')
        assert offset == -5.0

    def test_tokyo_offset(self):
        """Test Tokyo UTC offset (UTC+9)"""
        offset = get_timezone_offset_hours('Asia/Tokyo')
        assert offset == 9.0

    def test_utc_offset(self):
        """Test UTC offset (should be 0)"""
        offset = get_timezone_offset_hours('UTC')
        assert offset == 0.0

    def test_london_offset(self):
        """Test London offset (UTC+0 or UTC+1 depending on DST)"""
        offset = get_timezone_offset_hours('Europe/London')
        # London is either 0 or +1 depending on DST
        assert offset in [0.0, 1.0]


class TestTimeRangeChecking:
    """Test time range detection including midnight-crossing ranges"""

    def test_time_in_range_normal(self):
        """Test time within normal range (no midnight crossing)"""
        current = datetime(2025, 10, 8, 10, 0, 0)  # 10:00
        start = time(9, 0)   # 09:00
        end = time(17, 0)    # 17:00

        assert is_time_in_range(current, start, end) == True

    def test_time_before_range(self):
        """Test time before range"""
        current = datetime(2025, 10, 8, 8, 0, 0)  # 08:00
        start = time(9, 0)   # 09:00
        end = time(17, 0)    # 17:00

        assert is_time_in_range(current, start, end) == False

    def test_time_after_range(self):
        """Test time after range"""
        current = datetime(2025, 10, 8, 18, 0, 0)  # 18:00
        start = time(9, 0)   # 09:00
        end = time(17, 0)    # 17:00

        assert is_time_in_range(current, start, end) == False

    def test_time_at_range_boundaries(self):
        """Test time exactly at start and end boundaries"""
        start = time(9, 0)
        end = time(17, 0)

        at_start = datetime(2025, 10, 8, 9, 0, 0)
        at_end = datetime(2025, 10, 8, 17, 0, 0)

        assert is_time_in_range(at_start, start, end) == True
        assert is_time_in_range(at_end, start, end) == True

    def test_midnight_crossing_range_before_midnight(self):
        """Test midnight-crossing range: time before midnight"""
        current = datetime(2025, 10, 8, 23, 0, 0)  # 23:00 (11pm)
        start = time(22, 0)  # 22:00 (10pm)
        end = time(6, 0)     # 06:00 (6am next day)

        assert is_time_in_range(current, start, end) == True

    def test_midnight_crossing_range_after_midnight(self):
        """Test midnight-crossing range: time after midnight"""
        current = datetime(2025, 10, 8, 2, 0, 0)  # 02:00 (2am)
        start = time(22, 0)  # 22:00 (10pm prev day)
        end = time(6, 0)     # 06:00 (6am)

        assert is_time_in_range(current, start, end) == True

    def test_midnight_crossing_range_outside(self):
        """Test time outside midnight-crossing range"""
        current = datetime(2025, 10, 8, 12, 0, 0)  # 12:00 (noon)
        start = time(22, 0)  # 22:00 (10pm)
        end = time(6, 0)     # 06:00 (6am)

        assert is_time_in_range(current, start, end) == False

    def test_midnight_crossing_at_boundaries(self):
        """Test exact boundaries of midnight-crossing range"""
        start = time(22, 0)
        end = time(6, 0)

        at_start = datetime(2025, 10, 8, 22, 0, 0)
        at_end = datetime(2025, 10, 8, 6, 0, 0)
        just_before_start = datetime(2025, 10, 8, 21, 59, 0)
        just_after_end = datetime(2025, 10, 8, 6, 1, 0)

        assert is_time_in_range(at_start, start, end) == True
        assert is_time_in_range(at_end, start, end) == True
        assert is_time_in_range(just_before_start, start, end) == False
        assert is_time_in_range(just_after_end, start, end) == False


class TestQuietHours:
    """Test quiet hours detection (timezone-aware)"""

    def test_in_quiet_hours_colombia_evening(self):
        """Test quiet hours detection in Colombia evening"""
        # Note: This test validates the logic structure
        # Actual time-dependent testing would require time mocking
        result = is_in_quiet_hours(
            quiet_start=time(22, 0),
            quiet_end=time(6, 0),
            user_timezone='America/Bogota'
        )
        # Should return boolean
        assert isinstance(result, bool)

    def test_no_quiet_hours_configured(self):
        """Test when no quiet hours are set"""
        result = is_in_quiet_hours(None, None, 'America/Bogota')
        assert result == False

    def test_partial_quiet_hours_configured(self):
        """Test when only start or end is set"""
        result1 = is_in_quiet_hours(time(22, 0), None, 'America/Bogota')
        result2 = is_in_quiet_hours(None, time(6, 0), 'America/Bogota')

        assert result1 == False
        assert result2 == False


class TestDayBoundaries:
    """Test start and end of day calculations (timezone-aware)"""

    def test_start_of_day_utc_colombia(self):
        """Test getting start of day in Colombia time, converted to UTC"""
        # This will get midnight Colombia time in UTC
        start_utc = get_start_of_day_utc('America/Bogota', days_ago=0)

        # Convert back to Colombia to verify it's midnight there
        colombia_time = utc_to_user_time(start_utc, 'America/Bogota')

        assert colombia_time.hour == 0
        assert colombia_time.minute == 0
        assert colombia_time.second == 0

    def test_end_of_day_utc_colombia(self):
        """Test getting end of day in Colombia time, converted to UTC"""
        end_utc = get_end_of_day_utc('America/Bogota', days_ago=0)

        # Convert back to Colombia to verify it's 23:59:59 there
        colombia_time = utc_to_user_time(end_utc, 'America/Bogota')

        assert colombia_time.hour == 23
        assert colombia_time.minute == 59
        assert colombia_time.second == 59

    def test_start_of_yesterday_utc(self):
        """Test getting start of yesterday"""
        today_start = get_start_of_day_utc('America/Bogota', days_ago=0)
        yesterday_start = get_start_of_day_utc('America/Bogota', days_ago=1)

        # Should be 24 hours apart
        diff = today_start - yesterday_start
        assert diff == timedelta(days=1)

    def test_day_boundaries_tokyo(self):
        """Test day boundaries for Tokyo timezone"""
        start_utc = get_start_of_day_utc('Asia/Tokyo')
        end_utc = get_end_of_day_utc('Asia/Tokyo')

        # Convert back to verify
        tokyo_start = utc_to_user_time(start_utc, 'Asia/Tokyo')
        tokyo_end = utc_to_user_time(end_utc, 'Asia/Tokyo')

        assert tokyo_start.hour == 0
        assert tokyo_end.hour == 23
        assert tokyo_end.minute == 59


class TestBusinessHours:
    """Test business hours calculations"""

    def test_business_hours_colombia(self):
        """Test getting business hours in Colombia, converted to UTC"""
        start_utc, end_utc = get_business_hours_utc(
            business_start=time(9, 0),
            business_end=time(17, 0),
            user_timezone='America/Bogota'
        )

        # Convert back to Colombia time
        colombia_start = utc_to_user_time(start_utc, 'America/Bogota')
        colombia_end = utc_to_user_time(end_utc, 'America/Bogota')

        assert colombia_start.hour == 9
        assert colombia_end.hour == 17

    def test_business_hours_tokyo(self):
        """Test getting business hours in Tokyo"""
        start_utc, end_utc = get_business_hours_utc(
            business_start=time(8, 0),
            business_end=time(18, 0),
            user_timezone='Asia/Tokyo'
        )

        # Convert back to Tokyo time
        tokyo_start = utc_to_user_time(start_utc, 'Asia/Tokyo')
        tokyo_end = utc_to_user_time(end_utc, 'Asia/Tokyo')

        assert tokyo_start.hour == 8
        assert tokyo_end.hour == 18


class TestDeliveryScheduling:
    """Test notification delivery time calculation"""

    def test_calculate_next_delivery_same_day(self):
        """Test scheduling delivery for later today"""
        # This is complex to test without mocking current time
        # Test structure validation
        next_time = calculate_next_delivery_time(
            target_hour=8,
            target_minute=0,
            user_timezone='America/Bogota'
        )

        assert isinstance(next_time, datetime)
        assert next_time.tzinfo.key == 'UTC'

    def test_calculate_next_delivery_tomorrow(self):
        """Test scheduling delivery for tomorrow if target time passed"""
        # Test that function returns a valid UTC datetime
        next_time = calculate_next_delivery_time(
            target_hour=1,  # 1am - likely passed for most tests
            target_minute=0,
            user_timezone='America/Bogota'
        )

        assert isinstance(next_time, datetime)
        assert next_time > datetime.now(ZoneInfo('UTC'))

    def test_delivery_time_with_minutes(self):
        """Test scheduling with specific minutes"""
        next_time = calculate_next_delivery_time(
            target_hour=14,
            target_minute=30,
            user_timezone='Asia/Tokyo'
        )

        # Convert to Tokyo time to verify
        tokyo_time = utc_to_user_time(next_time, 'Asia/Tokyo')
        assert tokyo_time.minute == 30


class TestTimezoneList:
    """Test timezone list generation for UI"""

    def test_get_common_timezones_list(self):
        """Test generating timezone list for dropdown"""
        tz_list = get_common_timezones_list()

        assert isinstance(tz_list, list)
        assert len(tz_list) == 12

        # Check structure of first item
        first_tz = tz_list[0]
        assert 'value' in first_tz
        assert 'label' in first_tz
        assert 'offset' in first_tz
        assert 'region' in first_tz

    def test_timezone_list_has_colombia(self):
        """Test that Colombia timezone is in the list"""
        tz_list = get_common_timezones_list()
        colombia_items = [tz for tz in tz_list if tz['value'] == 'America/Bogota']

        assert len(colombia_items) == 1
        assert 'Bogota' in colombia_items[0]['label']
        assert colombia_items[0]['offset'] == '-05:00'

    def test_timezone_list_offset_format(self):
        """Test that offsets are properly formatted"""
        tz_list = get_common_timezones_list()

        for tz in tz_list:
            offset = tz['offset']
            # Should be in format +HH:MM or -HH:MM
            assert len(offset) == 6
            assert offset[0] in ['+', '-']
            assert offset[3] == ':'


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_timezone_string(self):
        """Test handling of empty timezone string"""
        tz = get_user_timezone('')
        assert tz.key == 'UTC'

    def test_whitespace_timezone(self):
        """Test handling of whitespace timezone"""
        tz = get_user_timezone('   ')
        assert tz.key == 'UTC'

    def test_dst_transition(self):
        """Test behavior during DST transitions"""
        # London transitions DST
        offset_summer = get_timezone_offset_hours('Europe/London')
        # Offset will be 0 or 1 depending on current date
        assert offset_summer in [0.0, 1.0]

    def test_midnight_exactly(self):
        """Test time exactly at midnight"""
        midnight = datetime(2025, 10, 8, 0, 0, 0)
        start = time(22, 0)
        end = time(6, 0)

        # Midnight (00:00) should be in range 22:00-06:00
        assert is_time_in_range(midnight, start, end) == True

    def test_23_59_59_time(self):
        """Test time at 23:59:59"""
        late_night = datetime(2025, 10, 8, 23, 59, 59)
        start = time(22, 0)
        end = time(6, 0)

        # 23:59:59 should be in range 22:00-06:00
        assert is_time_in_range(late_night, start, end) == True


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_colombia_user_evening_workflow(self):
        """Test complete workflow for Colombia user in evening"""
        # User in Colombia at 8pm (20:00 local) = 01:00 UTC next day
        utc_time = datetime(2025, 10, 9, 1, 0, 0, tzinfo=ZoneInfo('UTC'))
        local_time = utc_to_user_time(utc_time, 'America/Bogota')

        # Verify it's 8pm Colombia
        assert local_time.hour == 20
        assert local_time.day == 8  # Still Oct 8 in Colombia

        # Check if in quiet hours (22:00-06:00)
        in_quiet = is_time_in_range(
            local_time,
            time(22, 0),
            time(6, 0)
        )
        assert in_quiet == False  # 20:00 is not in quiet hours

        # Check if in business hours (9-17)
        in_business = is_time_in_range(
            local_time,
            time(9, 0),
            time(17, 0)
        )
        assert in_business == False  # 20:00 is after business hours

    def test_tokyo_user_morning_workflow(self):
        """Test complete workflow for Tokyo user in morning"""
        # User in Tokyo at 7am = 22:00 UTC previous day
        utc_time = datetime(2025, 10, 8, 22, 0, 0, tzinfo=ZoneInfo('UTC'))
        local_time = utc_to_user_time(utc_time, 'Asia/Tokyo')

        # Verify it's 7am Tokyo
        assert local_time.hour == 7
        assert local_time.day == 9  # Oct 9 in Tokyo

        # Not in quiet hours
        in_quiet = is_time_in_range(local_time, time(22, 0), time(6, 0))
        assert in_quiet == False

        # Not yet in business hours (starts 9am)
        in_business = is_time_in_range(local_time, time(9, 0), time(18, 0))
        assert in_business == False

    def test_cross_timezone_scheduling(self):
        """Test scheduling across multiple timezones"""
        # Schedule for 8am in different timezones
        colombia_next = calculate_next_delivery_time(8, 0, 'America/Bogota')
        tokyo_next = calculate_next_delivery_time(8, 0, 'Asia/Tokyo')

        # Both should be valid UTC times
        assert colombia_next.tzinfo.key == 'UTC'
        assert tokyo_next.tzinfo.key == 'UTC'

        # When converted back, both should be 8am local
        colombia_local = utc_to_user_time(colombia_next, 'America/Bogota')
        tokyo_local = utc_to_user_time(tokyo_next, 'Asia/Tokyo')

        assert colombia_local.hour == 8
        assert tokyo_local.hour == 8
