import structlog
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.db.client import db
from app.db.dao_leads import get_due_leads, update_lead_progress
from app.db.dao_sequences import get_campaign_sequence, get_sequence_step_by_id
from app.db.dao_templates import get_template
from app.db.dao_accounts import get_email_account, get_email_general_settings, get_email_campaign_settings
from app.db.dao_activities import insert_activity
from app.domain.arbiter import AccountArbiter
from app.domain.templating import render_template, append_signature
from app.domain.transport import SmtpSender
from app.config.settings import settings

log = structlog.get_logger()

_account_rr_cache = {}

def run_once(campaign_id: str, batch_size: int, dry_run: bool = False, since: datetime = None):
    """Process a batch of leads for a campaign"""
    now_utc = datetime.now(timezone.utc)
    leads = get_due_leads(campaign_id, now_utc, batch_size)
    if not leads:
        log.info("worker.no_due_leads", campaign_id=campaign_id)
        return
    
    sequence = get_campaign_sequence(campaign_id)
    if not sequence:
        log.error("worker.no_sequence", campaign_id=campaign_id)
        return
    steps = sequence.get("steps", [])
    
    # Get email accounts from campaign_options
    from app.db.dao_campaigns import get_campaign_options
    options = get_campaign_options(campaign_id)
    if not options:
        log.error("worker.no_options", campaign_id=campaign_id)
        return
    email_accounts = options.get("email_accounts", [])
    if not email_accounts:
        log.error("worker.no_accounts", campaign_id=campaign_id)
        return
    
    # Round-robin account selection per campaign
    rr = _account_rr_cache.setdefault(campaign_id, list(email_accounts))
    arbiter = AccountArbiter(db)
    
    processed = 0
    
    for lead in leads:
        progress = lead.get("progress", {})
        current_step_order = progress.get("current_step_order", 1)
        lead_id = str(lead["_id"]) if "_id" in lead else None
        
        # Find step info from the steps array in sequence
        step_info = next((s for s in steps if s.get("order") == current_step_order), None)
        if not step_info:
            # Completed sequence
            update_lead_progress(lead_id, {**progress, "stopped": True, "reason": "completed"})
            log.info("worker.sequence_completed", campaign_id=campaign_id, lead_id=lead_id)
            continue
        
        # Get the actual step document using the step id
        step_id = step_info.get("id")
        step = get_sequence_step_by_id(step_id) if step_id else None
        if not step:
            log.error("worker.no_step_document", campaign_id=campaign_id, lead_id=lead_id, step_id=step_id)
            continue
            
        template_id = step.get("active_template")
        if not template_id:
            log.error("worker.no_template_id", campaign_id=campaign_id, lead_id=lead_id, step_order=current_step_order, step=step)
            continue
        template = get_template(template_id)
        if not template:
            log.error("worker.no_template", campaign_id=campaign_id, lead_id=lead_id, template_id=template_id)
            continue
            
        # Handle lead_data - it can be array or object
        lead_data_raw = lead.get("lead_data", {})
        if isinstance(lead_data_raw, list) and lead_data_raw:
            # For lead_data arrays, we need to process each recipient separately
            # Check which recipients haven't been processed for this step yet
            progress = lead.get("progress", {})
            current_step_order = progress.get("current_step_order", 1)
            processed_recipients = progress.get("processed_recipients", {})
            
            # Find recipients that haven't been processed for current step
            recipients_to_process = []
            for i, recipient_data in enumerate(lead_data_raw):
                recipient_key = f"step_{current_step_order}_recipient_{i}"
                if recipient_key not in processed_recipients:
                    recipients_to_process.append((i, recipient_data))
            
            if not recipients_to_process:
                # All recipients for this step have been processed
                continue
                
            # Process the next recipient in line
            recipient_index, lead_data = recipients_to_process[0]
        else:
            lead_data = lead_data_raw
            recipient_index = 0  # Single recipient case
            
        # Account selection with round-robin (do this before template rendering to get account context)
        granted = False
        selected_email_id = None
        selected_account = None
        
        for _ in range(len(rr)):
            email_id = rr.pop(0)
            rr.append(email_id)
            
            account = get_email_account(email_id)
            if not account:
                log.warning("worker.account_not_found", email_id=email_id)
                continue
                
            settings_doc = get_email_campaign_settings(email_id)
            if not settings_doc:
                log.warning("worker.no_account_settings", email_id=email_id)
                continue
                
            daily_limit = int(settings_doc.get("daily_limit", 0))
            min_wait = int(settings_doc.get("min_wait_time", 0))
            
            if not arbiter.reserve(email_id, now_utc, daily_limit, min_wait):
                continue
                
            granted = True
            selected_email_id = email_id
            selected_account = account
            break
            
        if not granted:
            log.info("worker.no_account_available", campaign_id=campaign_id, lead_id=lead_id)
            break  # Stop processing this batch if no accounts available
            
        # Get account signature and general settings for template context
        sig_doc = get_email_general_settings(selected_email_id)
        
        # Enhance lead_data with account/sender information
        enhanced_lead_data = {
            **lead_data,
            # Account signature and sender info
            'account_signature': sig_doc.get("signature", "") if sig_doc else "",
            'sender_name': f"{sig_doc.get('first_name', '')} {sig_doc.get('last_name', '')}".strip() if sig_doc else "",
            'sender_first_name': sig_doc.get("first_name", "") if sig_doc else "",
            'sender_last_name': sig_doc.get("last_name", "") if sig_doc else "",
            'sender_email': selected_account.get("email", ""),
            # Campaign context
            'campaign_id': campaign_id,
            'step_order': current_step_order,
        }
            
        try:
            # Use 'content' field from template since that's what your schema has
            html_content = template.get("html") or template.get("content", "")
            subject, html = render_template(template["subject"], html_content, enhanced_lead_data)
            
            if not subject.strip():
                log.warning("worker.empty_subject", campaign_id=campaign_id, lead_id=lead_id, template_id=template_id)
                
        except Exception as e:
            log.error("worker.template_error", campaign_id=campaign_id, lead_id=lead_id, 
                     template_id=template_id, error=str(e), 
                     available_fields=list(enhanced_lead_data.keys()),
                     template_subject=template.get("subject", "")[:100])
            arbiter.rollback(selected_email_id, now_utc)
            continue
            
        # Get signature and append to email (if not already in template)
        signature = sig_doc.get("signature", "") if sig_doc else ""
        # Only append signature if it's not already included via {{account_signature}} in template
        if signature and "{{account_signature}}" not in template.get("content", ""):
            html = append_signature(html, signature)
            
        to_email = enhanced_lead_data.get("email")
        
        if not to_email:
            log.error("worker.no_email_address", campaign_id=campaign_id, lead_id=lead_id)
            arbiter.rollback(selected_email_id, now_utc)
            continue
        
        if dry_run:
            log.info("worker.dry_run_send", campaign_id=campaign_id, lead_id=lead_id, 
                    email_id=selected_email_id, to_email=to_email, subject=subject)
            arbiter.rollback(selected_email_id, now_utc)
            processed += 1
            continue
            
        # Send the email
        try:
            sender = SmtpSender(
                host=selected_account["smtp_host"],
                port=int(selected_account["smtp_port"]),
                username=selected_account["smtp_username"],
                password=selected_account.get("smtp_passcode") or selected_account.get("smtp_password"),
                starttls=settings.SMTP_STARTTLS
            )
            sender.send(selected_account, to_email, subject, html)
            
            # Commit the send
            min_wait = int(get_email_campaign_settings(selected_email_id).get("min_wait_time", 0))
            arbiter.commit(selected_email_id, now_utc, min_wait)
            
            # Update lead progress - track per-recipient processing
            progress = lead.get("progress", {})
            current_step_order = progress.get("current_step_order", 1)
            processed_recipients = progress.get("processed_recipients", {})
            
            # Mark this recipient as processed for this step
            recipient_key = f"step_{current_step_order}_recipient_{recipient_index}"
            processed_recipients[recipient_key] = {
                "processed_at": now_utc,
                "email": to_email,
                "template_id": template_id
            }
            
            # Check if all recipients for this step have been processed
            lead_data_raw = lead.get("lead_data", {})
            total_recipients = len(lead_data_raw) if isinstance(lead_data_raw, list) else 1
            
            recipients_processed_this_step = sum(1 for key in processed_recipients.keys() 
                                               if key.startswith(f"step_{current_step_order}_"))
            
            if recipients_processed_this_step >= total_recipients:
                # All recipients processed for this step - advance to next step
                next_due = now_utc + timedelta(days=step.get("next_message_day", 0))
                new_progress = {
                    **progress,
                    "current_step_order": current_step_order + 1,
                    "last_sent_at": now_utc,
                    "next_due_at": next_due,
                    "processed_recipients": processed_recipients
                }
                log.info("worker.step_completed", campaign_id=campaign_id, lead_id=lead_id, 
                        step_order=current_step_order, total_recipients=total_recipients)
            else:
                # More recipients to process for this step - set due time based on min_wait_time
                settings_doc = get_email_campaign_settings(selected_email_id)
                min_wait_minutes = int(settings_doc.get("min_wait_time", 0))
                next_due = now_utc + timedelta(minutes=min_wait_minutes)
                
                new_progress = {
                    **progress,
                    "last_sent_at": now_utc,
                    "next_due_at": next_due,
                    "processed_recipients": processed_recipients
                }
                log.info("worker.recipient_processed", campaign_id=campaign_id, lead_id=lead_id, 
                        step_order=current_step_order, 
                        recipients_done=recipients_processed_this_step, 
                        total_recipients=total_recipients,
                        next_due_minutes=min_wait_minutes)
            
            update_lead_progress(lead_id, new_progress)
            
            # Log activity
            insert_activity({
                "campaign_id": campaign_id,
                "lead_id": lead_id,
                "email_id": selected_email_id,
                "type": "sent",
                "meta": {"step_order": current_step_order, "template_id": template_id},
                "created_at": now_utc
            })
            
            log.info("worker.sent", campaign_id=campaign_id, lead_id=lead_id, 
                    email_id=selected_email_id, step_order=current_step_order, 
                    to_email=to_email, subject=subject)
            processed += 1
            
        except Exception as e:
            arbiter.rollback(selected_email_id, now_utc)
            insert_activity({
                "campaign_id": campaign_id,
                "lead_id": lead_id,
                "email_id": selected_email_id,
                "type": "error",
                "meta": {"step_order": current_step_order, "template_id": template_id, "reason": str(e)},
                "created_at": now_utc
            })
            log.error("worker.send_error", campaign_id=campaign_id, lead_id=lead_id, 
                     email_id=selected_email_id, error=str(e))
    
    log.info("worker.batch_complete", campaign_id=campaign_id, processed=processed, 
             total_leads=len(leads), dry_run=dry_run)
