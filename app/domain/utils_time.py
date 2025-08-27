from datetime import datetime, timezone
from typing import Optional
import pytz

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def to_campaign_tz(dt: datetime, tz_str: str) -> datetime:
    tz = pytz.timezone(tz_str.split()[0])
    return dt.astimezone(tz)
