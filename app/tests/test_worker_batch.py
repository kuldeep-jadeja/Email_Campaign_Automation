from mongomock import MongoClient
from datetime import datetime, timezone
from app.domain.worker import run_once
from app.db.dao_leads import update_lead_progress

def test_worker_happy_path():
    client = MongoClient()
    db = client['testdb']
    # Setup campaign, sequence, template, account, lead
    campaign_id = "c1"
    db.campaign_queue.insert_one({"campaign_id": campaign_id})
    db.campaign_sequences.insert_one({"campaign_id": campaign_id, "steps": [{"order": 1, "active_template": "t1", "next_message_day": 1}], "email_accounts": ["e1"]})
    db.sequence_steps.insert_one({"sequence_id": campaign_id, "order": 1, "active_template": "t1"})
    db.templates.insert_one({"_id": "t1", "subject": "Hello {{name}}", "html": "Hi {{name}}"})
    db.email_accounts.insert_one({"_id": "e1", "email": "sender@test.com", "smtp_host": "smtp.test.com", "smtp_port": 587, "smtp_username": "user", "smtp_password": "pass"})
    db.email_campaign_settings.insert_one({"email_id": "e1", "daily_limit": "10", "min_wait_time": "0"})
    db.email_general_settings.insert_one({"email_id": "e1", "signature": "<b>Best</b>"})
    db.campaign_leads.insert_one({"campaign_id": campaign_id, "lead_data": {"email": "lead@test.com", "name": "Test"}, "progress": {"current_step_order": 1, "stopped": False}})
    run_once(campaign_id, 1, dry_run=True)
    lead = db.campaign_leads.find_one({"lead_data.email": "lead@test.com"})
    assert lead["progress"]["current_step_order"] == 2
