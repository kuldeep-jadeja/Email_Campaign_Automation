from datetime import datetime, timedelta
from app.db.dao_runtime import atomic_reserve_account, commit_account_send, rollback_account_reservation
from app.config.settings import settings
import structlog

log = structlog.get_logger()

class AccountArbiter:
    def __init__(self, db):
        self.db = db

    def reserve(self, email_id: str, now_utc: datetime, daily_limit: int, min_wait_minutes: int) -> bool:
        """Reserve an account for sending if available"""
        date_key = now_utc.strftime('%Y-%m-%d')
        lock_until = now_utc + timedelta(seconds=settings.DEFAULT_RESERVATION_LOCK_SECONDS)
        
        state = atomic_reserve_account(email_id, date_key, now_utc, daily_limit, lock_until)
        
        if state and state.get("locked_until"):
            returned_lock = state.get("locked_until")
            # Make returned_lock timezone aware if it isn't
            if returned_lock.tzinfo is None:
                returned_lock = returned_lock.replace(tzinfo=lock_until.tzinfo)
            
            # Check if lock times are close (within 1 second) to account for MongoDB precision
            time_diff = abs((returned_lock - lock_until).total_seconds())
            if time_diff <= 1.0:
                log.debug("arbiter.reserved", email_id=email_id, date_key=date_key)
                return True
        
        log.debug("arbiter.denied", email_id=email_id, date_key=date_key, 
                 sent_count=state.get("sent_count") if state else None,
                 daily_limit=daily_limit)
        return False

    def commit(self, email_id: str, now_utc: datetime, min_wait_minutes: int):
        """Commit a successful send"""
        date_key = now_utc.strftime('%Y-%m-%d')
        next_available = now_utc + timedelta(minutes=min_wait_minutes)
        commit_account_send(email_id, date_key, next_available)
        log.debug("arbiter.committed", email_id=email_id, next_available=next_available)

    def rollback(self, email_id: str, now_utc: datetime):
        """Rollback a failed send"""
        date_key = now_utc.strftime('%Y-%m-%d')
        rollback_account_reservation(email_id, date_key)
        log.debug("arbiter.rolled_back", email_id=email_id)
