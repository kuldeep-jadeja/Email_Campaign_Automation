import pytest
from freezegun import freeze_time
from mongomock import MongoClient
from datetime import datetime, timezone
from app.domain.arbiter import AccountArbiter

@pytest.fixture
def db():
    client = MongoClient()
    return client['testdb']

@freeze_time("2025-08-27T10:00:00Z")
def test_reserve_atomic(db):
    arbiter = AccountArbiter(db)
    email_id = "test_email"
    now_utc = datetime.now(timezone.utc)
    daily_limit = 2
    min_wait = 0
    granted1 = arbiter.reserve(email_id, now_utc, daily_limit, min_wait)
    granted2 = arbiter.reserve(email_id, now_utc, daily_limit, min_wait)
    assert granted1 != granted2

@freeze_time("2025-08-27T10:00:00Z")
def test_daily_cap(db):
    arbiter = AccountArbiter(db)
    email_id = "test_email"
    now_utc = datetime.now(timezone.utc)
    daily_limit = 1
    min_wait = 0
    assert arbiter.reserve(email_id, now_utc, daily_limit, min_wait)
    arbiter.commit(email_id, now_utc, min_wait)
    assert not arbiter.reserve(email_id, now_utc, daily_limit, min_wait)

@freeze_time("2025-08-27T10:00:00Z")
def test_cooldown(db):
    arbiter = AccountArbiter(db)
    email_id = "test_email"
    now_utc = datetime.now(timezone.utc)
    daily_limit = 2
    min_wait = 10
    assert arbiter.reserve(email_id, now_utc, daily_limit, min_wait)
    arbiter.commit(email_id, now_utc, min_wait)
    assert not arbiter.reserve(email_id, now_utc, daily_limit, min_wait)
