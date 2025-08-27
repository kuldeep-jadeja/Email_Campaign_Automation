from app.db.client import db
from typing import Dict

def insert_activity(activity: Dict):
    db.campaign_activities.insert_one(activity)
