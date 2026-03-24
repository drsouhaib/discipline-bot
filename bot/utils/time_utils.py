import pytz
from datetime import datetime, time, timedelta
from typing import Optional

def get_current_time_in_timezone(timezone_str: str) -> datetime:
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz)

def parse_time_string(time_str: str) -> Optional[time]:
    """Parse HH:MM or HH:MM:SS to time object."""
    try:
        parts = time_str.split(":")
        if len(parts) == 2:
            return time(hour=int(parts[0]), minute=int(parts[1]))
        elif len(parts) == 3:
            return time(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2]))
    except:
        pass
    return None

def format_time_for_user(dt: datetime, tz_str: str) -> str:
    """Format datetime to user's local time string (HH:MM)."""
    tz = pytz.timezone(tz_str)
    local = dt.astimezone(tz)
    return local.strftime("%H:%M")

def get_next_morning_datetime(user_tz: str, wake_up_time_str: str) -> datetime:
    """Get next datetime for morning sequence."""
    tz = pytz.timezone(user_tz)
    now = datetime.now(tz)
    target_time = parse_time_string(wake_up_time_str)
    if target_time is None:
        target_time = time(7, 0)
    target_dt = tz.localize(datetime.combine(now.date(), target_time))
    if target_dt <= now:
        target_dt += timedelta(days=1)
    return target_dt