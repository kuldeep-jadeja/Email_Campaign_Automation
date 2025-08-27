from app.db.client import db
from pymongo import ASCENDING, DESCENDING

def ensure_indexes():
    db.campaigns.create_index([("status", ASCENDING)])
    db.campaign_options.create_index([("campaign_id", ASCENDING)], unique=True)
    db.campaign_schedule.create_index([("campaign_id", ASCENDING)], unique=True)
    db.campaign_sequences.create_index([("campaign_id", ASCENDING)], unique=True)
    db.sequence_steps.create_index([("sequence_id", ASCENDING), ("_id", ASCENDING)])
    db.templates.create_index([("user_id", ASCENDING)])
    db.campaign_leads.create_index([("campaign_id", ASCENDING)])
    db.campaign_leads.create_index([("lead_data.email", ASCENDING)])
    db.campaign_leads.create_index([("progress.stopped", ASCENDING), ("progress.next_due_at", ASCENDING)])
    db.campaign_activities.create_index([("campaign_id", ASCENDING), ("created_at", DESCENDING)])
    db.campaign_activities.create_index([("lead_id", ASCENDING), ("created_at", DESCENDING)])
    db.campaign_activities.create_index([("email_id", ASCENDING), ("created_at", DESCENDING)])
    db.account_runtime_state.create_index([("email_id", ASCENDING), ("date_key", ASCENDING)], unique=True)
