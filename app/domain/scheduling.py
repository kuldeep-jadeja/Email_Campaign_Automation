import pytz
from datetime import datetime, time
from typing import Dict

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

def in_window(now_utc: datetime, schedule_doc: Dict) -> bool:
    tz_str = schedule_doc.get("timezone")
    if not tz_str:
        return False
    try:
        tz = pytz.timezone(tz_str.split()[0])
    except Exception:
        return False
    now_local = now_utc.astimezone(tz)
    weekday = now_local.strftime("%A").lower()
    scheduled_days = schedule_doc.get("scheduled_days", WEEKDAYS)
    if weekday not in [d.lower() for d in scheduled_days]:
        return False
    import re
    def parse_date(val):
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            # Try ISO8601, with or without Z
            m = re.match(r"(\d{4}-\d{2}-\d{2})", val)
            if m:
                return datetime.fromisoformat(m.group(1)).date()
            try:
                return datetime.fromisoformat(val.replace('Z','')).date()
            except Exception:
                pass
        return None
    start_date = parse_date(schedule_doc.get("start_date"))
    end_date = parse_date(schedule_doc.get("end_date"))
    today = now_local.date()
    if start_date and today < start_date:
        return False
    if end_date and today > end_date:
        return False
    time_from = schedule_doc.get("time_from")
    time_to = schedule_doc.get("time_to")
    if not (time_from and time_to):
        return True
    
    def parse_time(time_str):
        # Handle AM/PM format like "01:00 pm"
        if 'am' in time_str.lower() or 'pm' in time_str.lower():
            return datetime.strptime(time_str, "%I:%M %p").time()
        # Handle ISO format like "13:00"
        return time.fromisoformat(time_str)
    
    t_from = parse_time(time_from)
    t_to = parse_time(time_to)
    now_t = now_local.time()
    if t_from <= t_to:
        return t_from <= now_t <= t_to
    else:
        return now_t >= t_from or now_t <= t_to
