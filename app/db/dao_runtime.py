from app.db.client import db
from typing import Optional
from datetime import datetime
from pymongo import ReturnDocument

def get_account_runtime_state(email_id: str, date_key: str) -> Optional[dict]:
    return db.account_runtime_state.find_one({"email_id": email_id, "date_key": date_key})

def atomic_reserve_account(email_id: str, date_key: str, now_utc: datetime, 
                          daily_limit: int, lock_until: datetime) -> Optional[dict]:
    """Atomically reserve an account if available"""
    # For new records, set next_available_at to beginning of today (so they're immediately available)
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return db.account_runtime_state.find_one_and_update(
        {
            "email_id": email_id,
            "date_key": date_key,
            "sent_count": {"$lt": daily_limit},
            "$and": [
                {
                    "$or": [
                        {"locked_until": {"$exists": False}},
                        {"locked_until": {"$lte": now_utc}}
                    ]
                },
                {
                    "$or": [
                        {"next_available_at": {"$exists": False}},
                        {"next_available_at": {"$lte": now_utc}}
                    ]
                }
            ]
        },
        {
            "$setOnInsert": {
                "sent_count": 0, 
                "next_available_at": start_of_day  # Set to start of day for new records
            },
            "$set": {"locked_until": lock_until}
            # Don't update next_available_at during reservation - only during commit
        },
        upsert=True, 
        return_document=ReturnDocument.AFTER
    )

def commit_account_send(email_id: str, date_key: str, next_available: datetime):
    """Commit a successful send"""
    db.account_runtime_state.update_one(
        {"email_id": email_id, "date_key": date_key},
        {
            "$inc": {"sent_count": 1},
            "$set": {"next_available_at": next_available, "locked_until": None}
        }
    )

def rollback_account_reservation(email_id: str, date_key: str):
    """Rollback a failed send"""
    db.account_runtime_state.update_one(
        {"email_id": email_id, "date_key": date_key},
        {"$set": {"locked_until": None}}
    )

def recount_account_runtime_state(email_id: str, date_key: str):
    """Rebuild runtime state from activities"""
    from datetime import datetime
    start_of_day = datetime.fromisoformat(f"{date_key}T00:00:00+00:00")
    end_of_day = datetime.fromisoformat(f"{date_key}T23:59:59+00:00")
    
    sent_count = db.campaign_activities.count_documents({
        "email_id": email_id,
        "type": "sent",
        "created_at": {"$gte": start_of_day, "$lte": end_of_day}
    })
    
    db.account_runtime_state.update_one(
        {"email_id": email_id, "date_key": date_key},
        {"$set": {"sent_count": sent_count}},
        upsert=True
    )
