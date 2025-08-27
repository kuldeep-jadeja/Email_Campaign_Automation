import typer
from datetime import datetime
from app.db.indexes import ensure_indexes
from app.domain.dispatcher import run_once as dispatcher_run_once
from app.domain.worker import run_once as worker_run_once
from app.db.dao_leads import backfill_lead_progress
from app.db.dao_runtime import recount_account_runtime_state
from app.db.dao_accounts import get_all_email_accounts
from app.config.settings import settings

app = typer.Typer()

@app.command()
def init_indexes():
    """Create all MongoDB indexes."""
    ensure_indexes()
    typer.echo("Indexes created successfully.")

@app.command()
def run_continuous(
    tick_seconds: int = typer.Option(settings.DISPATCHER_TICK_SECONDS, help="Seconds between dispatcher runs"),
    batch_size: int = typer.Option(settings.DEFAULT_WORKER_BATCH_SIZE, help="Batch size for each worker"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """Run the dispatcher continuously."""
    import time
    
    if verbose:
        import structlog
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    typer.echo(f"Starting continuous dispatcher with {tick_seconds}s intervals...")
    typer.echo("Press Ctrl+C to stop")
    
    try:
        while True:
            try:
                typer.echo(f"\n--- Running dispatcher at {datetime.now()} ---")
                dispatcher_run_once(batch_size=batch_size, verbose=verbose)
                typer.echo("Dispatcher run completed.")
                
                typer.echo(f"Sleeping for {tick_seconds} seconds...")
                time.sleep(tick_seconds)
                
            except KeyboardInterrupt:
                typer.echo("\nReceived interrupt signal. Stopping...")
                break
            except Exception as e:
                typer.echo(f"Error in dispatcher run: {e}")
                typer.echo(f"Continuing after {tick_seconds} seconds...")
                time.sleep(tick_seconds)
                
    except KeyboardInterrupt:
        typer.echo("\nDispatcher stopped.")


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

@app.command()
def list_campaigns():
    """List all campaigns."""
    from app.db.client import db
    
    campaigns = list(db.campaigns.find({}).limit(10))
    
    if not campaigns:
        typer.echo("No campaigns found.")
        return
        
    typer.echo(f"Found {db.campaigns.count_documents({})} campaigns (showing first 10):")
    typer.echo()
    
    for campaign in campaigns:
        campaign_id = campaign.get("_id")
        name = campaign.get("name", "Unnamed")
        status = campaign.get("status", "unknown")
        created = campaign.get("created_date", "unknown")
        
        typer.echo(f"  {campaign_id}")
        typer.echo(f"    Name: {name}")
        typer.echo(f"    Status: {status}")
        typer.echo(f"    Created: {created}")
        typer.echo()


@app.command()
def make_lead_due_now(
    lead_id: str = typer.Argument(..., help="Lead ID to make due now"),
):
    """Make a specific lead due now for testing."""
    from app.db.client import db
    from bson import ObjectId
    from datetime import datetime, timezone
    
    try:
        # Find the lead
        lead = db.campaign_leads.find_one({"_id": ObjectId(lead_id)})
        if not lead:
            typer.echo(f"Lead {lead_id} not found.")
            return
            
        # Update next_due_at to now
        now_utc = datetime.now(timezone.utc)
        result = db.campaign_leads.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": {"progress.next_due_at": now_utc.replace(tzinfo=None)}}
        )
        
        if result.modified_count > 0:
            typer.echo(f"Lead {lead_id} is now due for processing.")
            
            # Show updated progress
            updated_lead = db.campaign_leads.find_one({"_id": ObjectId(lead_id)})
            progress = updated_lead.get("progress", {})
            current_step = progress.get("current_step_order", "unknown")
            typer.echo(f"Current step: {current_step}")
            typer.echo(f"Next due: {progress.get('next_due_at', 'unknown')}")
        else:
            typer.echo("Failed to update lead.")
            
    except Exception as e:
        typer.echo(f"Error: {e}")


@app.command()
def show_lead_details(
    lead_id: str = typer.Argument(..., help="Lead ID to show details for"),
):
    """Show detailed information about a specific lead."""
    from app.db.client import db
    from bson import ObjectId
    from datetime import datetime, timezone
    
    try:
        # Find the lead
        lead = db.campaign_leads.find_one({"_id": ObjectId(lead_id)})
        if not lead:
            typer.echo(f"Lead {lead_id} not found.")
            return
            
        campaign_id = lead.get("campaign_id", "unknown")
        progress = lead.get("progress", {})
        lead_data = lead.get("lead_data", [])
        
        typer.echo(f"Lead ID: {lead_id}")
        typer.echo(f"Campaign ID: {campaign_id}")
        typer.echo()
        
        typer.echo("Lead Data:")
        for i, data in enumerate(lead_data):
            email = data.get("email", "no email")
            name = data.get("name", "no name")
            status = data.get("status", "no status")
            typer.echo(f"  [{i}] {email} - {name} - {status}")
        typer.echo()
        
        typer.echo("Progress:")
        current_step = progress.get("current_step_order", "not set")
        last_sent = progress.get("last_sent_at", "never")
        next_due = progress.get("next_due_at", "not set")
        stopped = progress.get("stopped", False)
        
        typer.echo(f"  Current step: {current_step}")
        typer.echo(f"  Last sent: {last_sent}")
        typer.echo(f"  Next due: {next_due}")
        typer.echo(f"  Stopped: {stopped}")
        
        # Check if due now
        if next_due and next_due != "not set":
            now_utc = datetime.now(timezone.utc)
            if isinstance(next_due, datetime):
                if next_due.tzinfo is None:
                    next_due = next_due.replace(tzinfo=timezone.utc)
                is_due = next_due <= now_utc
                time_diff = next_due - now_utc
                typer.echo(f"  Is due now: {is_due}")
                if not is_due:
                    typer.echo(f"  Time until due: {time_diff}")
        
    except Exception as e:
        typer.echo(f"Error: {e}")


@app.command()
def reset_lead_progress(
    lead_id: str = typer.Argument(..., help="Lead ID to reset"),
):
    """Reset a lead's progress to start from step 1."""
    from app.db.client import db
    from bson import ObjectId
    
    try:
        # Reset the lead to step 1 with empty recipient tracking
        result = db.campaign_leads.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": {"progress": {
                "current_step_order": 1, 
                "stopped": False,
                "processed_recipients": {}
            }}}
        )
        
        if result.modified_count > 0:
            typer.echo(f"Lead {lead_id} progress reset to step 1.")
            typer.echo("All recipients will be processed from the beginning.")
        else:
            typer.echo("Lead not found or no changes made.")
            
    except Exception as e:
        typer.echo(f"Error: {e}")


@app.command()
def list_leads():
    """List campaign leads."""
    from app.db.client import db
    
    leads = list(db.campaign_leads.find({}).limit(10))
    
    if not leads:
        typer.echo("No leads found.")
        return
        
    typer.echo(f"Found {db.campaign_leads.count_documents({})} leads (showing first 10):")
    typer.echo()
    
    for lead in leads:
        lead_id = lead.get("_id")
        campaign_id = lead.get("campaign_id")
        email = lead.get("email", "unknown")
        status = lead.get("status", "unknown")
        
        typer.echo(f"  {lead_id}")
        typer.echo(f"    Campaign: {campaign_id}")
        typer.echo(f"    Email: {email}")
        typer.echo(f"    Status: {status}")
        typer.echo()


if __name__ == "__main__":
    app()
