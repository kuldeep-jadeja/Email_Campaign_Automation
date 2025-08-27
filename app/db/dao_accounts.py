from app.db.client import db
from bson import ObjectId
from typing import Optional

def get_email_account(email_id: str) -> Optional[dict]:
    return db.email_accounts.find_one({"_id": ObjectId(email_id)})

def get_email_campaign_settings(email_id: str) -> Optional[dict]:
    return db.email_campaign_settings.find_one({"email_id": email_id})

def get_email_general_settings(email_id: str) -> Optional[dict]:
    return db.email_general_settings.find_one({"email_id": email_id})

def get_all_email_accounts() -> list:
    return list(db.email_accounts.find({"status": "active"}))
