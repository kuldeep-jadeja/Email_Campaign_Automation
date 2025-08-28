from app.db.client import db
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

def get_due_leads(campaign_id: str, now_utc: datetime, batch_size: int) -> List[dict]:
    query = {
        "campaign_id": ObjectId(campaign_id),  # Convert string to ObjectId
        "$or": [
            {"progress": {"$exists": False}},  # No progress means never sent
            {
                "progress.stopped": {"$ne": True},
                "$or": [
                    {"progress.next_due_at": {"$lte": now_utc}},
                    {"progress.last_sent_at": {"$exists": False}}
                ]
            }
        ]
    }
    return list(db.campaign_leads.find(query, {"lead_data": 1, "progress": 1}).limit(batch_size))

def update_lead_progress(lead_id: str, progress: dict):
    db.campaign_leads.update_one({"_id": ObjectId(lead_id)}, {"$set": {"progress": progress}})

def backfill_lead_progress(campaign_id: str):
    """Add default progress to leads that don't have it"""
    db.campaign_leads.update_many(
        {"campaign_id": campaign_id, "progress": {"$exists": False}},
        {"$set": {"progress": {"current_step_order": 1, "stopped": False}}}
    )
