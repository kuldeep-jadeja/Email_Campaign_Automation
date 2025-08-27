import structlog
from datetime import datetime, timezone
from app.db.dao_campaigns import get_campaign_queue, get_campaign_by_id, get_campaign_options, get_campaign_schedule, get_campaign_daily_sent_count
from app.domain.scheduling import in_window
from app.domain.worker import run_once as worker_run_once
from app.config.settings import settings

log = structlog.get_logger()

def run_once(batch_size: int = None, verbose: bool = False):
    """Run dispatcher once - check all campaigns in queue and dispatch workers"""
    now_utc = datetime.now(timezone.utc)
    batch_size = batch_size or settings.DEFAULT_WORKER_BATCH_SIZE
    queue = get_campaign_queue()
    
    if not queue:
        if verbose:
            log.info("dispatcher.no_campaigns_in_queue")
        return
    
    for campaign_entry in queue:
        campaign_id = str(campaign_entry["campaign_id"])
        
        # Check if campaign exists and is active
        campaign = get_campaign_by_id(campaign_id)
        if not campaign:
            log.warning("dispatcher.campaign_not_found", campaign_id=campaign_id)
            continue
            
        if campaign.get("status") != "active":
            if verbose:
                log.info("dispatcher.campaign_not_active", campaign_id=campaign_id, status=campaign.get("status"))
            continue
        
        # Check schedule window
        schedule = get_campaign_schedule(campaign_id)
        if not schedule:
            log.warning("dispatcher.no_schedule", campaign_id=campaign_id)
            continue
            
        if not in_window(now_utc, schedule):
            if verbose:
                log.info("dispatcher.skip_schedule", campaign_id=campaign_id, 
                        timezone=schedule.get("timezone"), 
                        scheduled_days=schedule.get("scheduled_days"))
            continue
        
        # Check campaign daily limits
        options = get_campaign_options(campaign_id)
        if not options:
            log.error("dispatcher.no_options", campaign_id=campaign_id)
            continue
            
        daily_limit = int(options.get("daily_email_limit", 0))
        if daily_limit <= 0:
            if verbose:
                log.info("dispatcher.no_daily_limit", campaign_id=campaign_id)
            continue
            
        day_start_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = get_campaign_daily_sent_count(campaign_id, day_start_utc)
        
        if sent_today >= daily_limit:
            if verbose:
                log.info("dispatcher.daily_limit_reached", campaign_id=campaign_id, 
                        sent_today=sent_today, daily_limit=daily_limit)
            continue
        
        # Calculate remaining budget for this batch
        remaining_budget = daily_limit - sent_today
        effective_batch_size = min(batch_size, remaining_budget)
        
        if verbose:
            log.info("dispatcher.dispatching_worker", campaign_id=campaign_id, 
                    batch_size=effective_batch_size, sent_today=sent_today, 
                    daily_limit=daily_limit)
        
        # Dispatch worker for this campaign
        try:
            worker_run_once(campaign_id, effective_batch_size, dry_run=False)
        except Exception as e:
            log.error("dispatcher.worker_error", campaign_id=campaign_id, error=str(e))
