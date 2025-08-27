from app.db.client import db
from bson import ObjectId
from typing import Any, Optional, List

def get_campaign_queue():
    return list(db.campaign_queue.find({}))

def get_campaign_by_id(campaign_id: str) -> Optional[dict]:
    return db.campaigns.find_one({"_id": ObjectId(campaign_id)})

def get_campaign_options(campaign_id: str) -> Optional[dict]:
    return db.campaign_options.find_one({"campaign_id": campaign_id})

def get_campaign_schedule(campaign_id: str) -> Optional[dict]:
    return db.campaign_schedule.find_one({"campaign_id": campaign_id})

def get_campaign_daily_sent_count(campaign_id: str, day_start_utc) -> int:
    """Count emails sent today for this campaign"""
    return db.campaign_activities.count_documents({
        "campaign_id": campaign_id,
        "type": "sent",
        "created_at": {"$gte": day_start_utc}
    })
