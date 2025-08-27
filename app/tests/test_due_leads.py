from datetime import datetime, timezone, timedelta
from app.db.dao_leads import get_due_leads
from mongomock import MongoClient


def test_due_leads_selection():
    client = MongoClient()
    db = client['testdb']
    now_utc = datetime.now(timezone.utc)
    db.campaign_leads.insert_many([
        {
            "campaign_id": "c1",
            "lead_data": {"email": "a@test.com"},
            "progress": {"stopped": False, "next_due_at": now_utc - timedelta(minutes=1)}
        },
        {
            "campaign_id": "c1",
            "lead_data": {"email": "b@test.com"},
            "progress": {"stopped": True, "next_due_at": now_utc}
        },
        {
            "campaign_id": "c1",
            "lead_data": {"email": "c@test.com"},
            "progress": {"stopped": False}
        }
    ])
    leads = get_due_leads("c1", now_utc, 10)
    emails = [l["lead_data"]["email"] for l in leads]
    assert "a@test.com" in emails
    assert "c@test.com" in emails
    assert "b@test.com" not in emails
