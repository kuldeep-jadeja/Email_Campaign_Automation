from app.db.client import db
from bson import ObjectId
from typing import Optional

def get_campaign_sequence(campaign_id: str) -> Optional[dict]:
    return db.campaign_sequences.find_one({"campaign_id": campaign_id})

def get_sequence_step_by_id(step_id: str) -> Optional[dict]:
    return db.sequence_steps.find_one({"_id": ObjectId(step_id)})
