import typer
from datetime import datetime
from app.db.indexes import ensure_indexes
from app.domain.dispatcher import run_once as dispatcher_run_once
from app.domain.worker import run_once as worker_run_once
from app.db.dao_leads import backfill_lead_progress
from app.db.dao_runtime import recount_account_runtime_state
from app.db.dao_accounts import get_all_email_accounts

app = typer.Typer()

@app.command()
def init_indexes():
    """Create all MongoDB indexes."""
    ensure_indexes()
    typer.echo("Indexes created successfully.")

@app.command()
def run_dispatcher(tick_seconds: int = 15, batch_size: int = 20, verbose: bool = False):
    """Run the global dispatcher once."""
    dispatcher_run_once(batch_size, verbose)
    typer.echo("Dispatcher run completed.")

@app.command()
def run_worker(campaign: str, batch_size: int = 20, dry_run: bool = False, since: str = None):
    """Run worker for a specific campaign."""
    since_dt = datetime.fromisoformat(since) if since else None
    worker_run_once(campaign, batch_size, dry_run, since_dt)
    typer.echo(f"Worker run completed for campaign {campaign}.")

@app.command()
def backfill_progress(campaign: str):
    """Add default progress to existing leads without progress."""
    backfill_lead_progress(campaign)
    typer.echo(f"Progress backfilled for campaign {campaign}.")

@app.command()
def recount_runtime(email_id: str, date: str):
    """Rebuild runtime state from activities for an account on a specific date."""
    recount_account_runtime_state(email_id, date)
    typer.echo(f"Runtime state recounted for {email_id} on {date}.")

@app.command() 
def check_runtime_states():
    """Check current account runtime states."""
    from app.db.client import db
    from datetime import datetime, timezone
    
    now_utc = datetime.now(timezone.utc)
    
    # Get all runtime states
    states = list(db.account_runtime_state.find({}))
    
    if not states:
        typer.echo("No runtime states found.")
        return
        
    typer.echo(f"Found {len(states)} runtime state records:")
    
    for state in states:
        email_id = state["email_id"]
        next_available = state["next_available_at"]
        sent_count = state.get("sent_count", 0)
        locked_until = state.get("locked_until")
        
        # Ensure datetimes are timezone-aware for comparison
        if next_available and next_available.tzinfo is None:
            next_available = next_available.replace(tzinfo=timezone.utc)
        if locked_until and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        
        # Get account info
        from bson import ObjectId
        try:
            if isinstance(email_id, str):
                account = db.email_accounts.find_one({"_id": ObjectId(email_id)})
            else:
                account = db.email_accounts.find_one({"_id": email_id})
        except:
            account = None
            
        email = account["email"] if account else "unknown"
        
        # Get daily_limit from campaign settings (this is what the worker uses)
        campaign_settings = db.email_campaign_settings.find_one({"email_id": email_id})
        daily_limit = int(campaign_settings.get("daily_limit", 0)) if campaign_settings else 0
        
        status = "AVAILABLE" if next_available <= now_utc else "WAITING"
        if locked_until and locked_until > now_utc:
            status = "LOCKED"
            
        typer.echo(f"  {email} ({email_id}): {status}")
        typer.echo(f"    Daily limit: {daily_limit}, Sent today: {sent_count}")
        typer.echo(f"    Next available: {next_available}")
        if locked_until:
            typer.echo(f"    Locked until: {locked_until}")
        typer.echo()


@app.command() 
def fix_runtime_states():
    """Fix account runtime states with next_available_at in the past."""
    from app.db.client import db
    from datetime import datetime, timezone, timedelta
    
    now_utc = datetime.now(timezone.utc)
    start_of_today = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Find problematic records (anything before 2020 is definitely wrong)
    problematic = db.account_runtime_state.find({
        "next_available_at": {"$lt": datetime(2020, 1, 1, tzinfo=timezone.utc)}
    })
    
    count = 0
    for record in problematic:
        # Update next_available_at to start of today (makes them immediately available)
        db.account_runtime_state.update_one(
            {"_id": record["_id"]},
            {"$set": {"next_available_at": start_of_today, "locked_until": None}}
        )
        count += 1
        
    typer.echo(f"Fixed {count} problematic runtime state records.")
    
    # Also fix any records with future next_available_at that seem wrong
    future_problematic = db.account_runtime_state.find({
        "next_available_at": {"$gt": now_utc + timedelta(hours=1)},
        "sent_count": 0
    })
    
    future_count = 0
    for record in future_problematic:
        db.account_runtime_state.update_one(
            {"_id": record["_id"]},
            {"$set": {"next_available_at": start_of_today, "locked_until": None}}
        )
        future_count += 1
    
    if future_count > 0:
        typer.echo(f"Also fixed {future_count} records with suspicious future timestamps.")

@app.command()
def send_one(campaign: str, lead: str, account: str, dry_run: bool = True):
    """Send one email for debugging (not implemented - use worker with batch-size 1)."""
    typer.echo("Use 'run-worker' with --batch-size 1 for single email testing.")

@app.command()
def list_accounts():
    """List all active email accounts."""
    accounts = get_all_email_accounts()
    for account in accounts:
        typer.echo(f"ID: {account['_id']}, Email: {account['email']}, Status: {account.get('status', 'unknown')}")

@app.command()
def debug_template(campaign: str, lead_id: str = None):
    """Debug template rendering for a campaign and lead."""
    from app.db.dao_leads import get_due_leads
    from app.db.dao_sequences import get_campaign_sequence, get_sequence_step_by_id
    from app.db.dao_templates import get_template
    from app.domain.templating import render_template
    from datetime import datetime, timezone
    from bson import ObjectId
    
    now_utc = datetime.now(timezone.utc)
    
    if lead_id:
        from app.db.client import db
        lead = db.campaign_leads.find_one({"_id": ObjectId(lead_id)})
        leads = [lead] if lead else []
    else:
        leads = get_due_leads(campaign, now_utc, 1)
    
    if not leads:
        typer.echo(f"No leads found for campaign {campaign}")
        return
        
    lead = leads[0]
    lead_data_raw = lead.get("lead_data", {})
    if isinstance(lead_data_raw, list) and lead_data_raw:
        lead_data = lead_data_raw[0]
    else:
        lead_data = lead_data_raw
        
    typer.echo(f"Lead ID: {lead['_id']}")
    typer.echo(f"Available lead fields: {list(lead_data.keys())}")
    typer.echo(f"Lead data: {lead_data}")
    
    sequence = get_campaign_sequence(campaign)
    if not sequence:
        typer.echo("No sequence found")
        return
        
    progress = lead.get("progress", {})
    current_step_order = progress.get("current_step_order", 1)
    step_info = next((s for s in sequence.get("steps", []) if s.get("order") == current_step_order), None)
    
    if not step_info:
        typer.echo(f"No step found for order {current_step_order}")
        return
        
    step = get_sequence_step_by_id(step_info.get("id"))
    if not step:
        typer.echo("Step document not found")
        return
        
    template = get_template(step.get("active_template"))
    if not template:
        typer.echo("Template not found")
        return
        
    typer.echo(f"\nTemplate ID: {template['_id']}")
    typer.echo(f"Template subject: {template.get('subject', '')}")
    typer.echo(f"Template content preview: {template.get('content', '')[:200]}...")
    
    try:
        html_content = template.get("html") or template.get("content", "")
        subject, html = render_template(template["subject"], html_content, lead_data)
        typer.echo(f"\nRendered subject: {subject}")
        typer.echo(f"Rendered HTML preview: {html[:200]}...")
    except Exception as e:
        typer.echo(f"Template render error: {e}")

@app.command()
def continuous_dispatcher(tick_seconds: int = 15, batch_size: int = 20, verbose: bool = False):
    """Run dispatcher continuously with specified tick interval."""
    import time
    typer.echo(f"Starting continuous dispatcher with {tick_seconds}s intervals...")
    try:
        while True:
            dispatcher_run_once(batch_size, verbose)
            time.sleep(tick_seconds)
    except KeyboardInterrupt:
        typer.echo("Dispatcher stopped.")

if __name__ == "__main__":
    app()
