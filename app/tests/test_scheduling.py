from datetime import datetime, timezone
from app.domain.scheduling import in_window

def test_in_window_basic():
    schedule = {
        "timezone": "Asia/Kolkata (UTC +05:30)",
        "weekdays": ["monday"],
        "time_from": "10:00",
        "time_to": "16:00",
        "start_date": datetime(2025, 8, 25).date(),
        "end_date": datetime(2025, 8, 30).date()
    }
    dt = datetime(2025, 8, 25, 9, 59, tzinfo=timezone.utc)
    assert not in_window(dt, schedule)
    dt = datetime(2025, 8, 25, 10, 1, tzinfo=timezone.utc)
    assert in_window(dt, schedule)
