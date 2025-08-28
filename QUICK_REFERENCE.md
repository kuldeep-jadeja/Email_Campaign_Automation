# Quick Reference Guide

## Essential Commands

### 🚀 Start Email Processing

```bash
# Run the main dispatcher
python -m app.cli.main run-dispatcher --verbose

# Dry run (no actual emails)
python -m app.cli.main run-dispatcher --dry-run --verbose
```

### 📊 Check System Status

```bash
# Show leads ready for processing
python -m app.cli.main show-due-leads

# View specific lead details
python -m app.cli.main show-lead-details <lead_id>

# List all campaigns
python -m app.cli.main list-campaigns

# List email accounts
python -m app.cli.main list-accounts
```

### 🔧 Lead Management

```bash
# Reset lead progress (starts over)
python -m app.cli.main reset-lead-progress <lead_id>

# Update all lead statuses
python -m app.cli.main update-lead-statuses
```

### 🐛 Debugging

```bash
# Test template rendering
python -m app.cli.main debug-template <campaign_id> --lead-id <lead_id>

# Test database connection
python -c "from app.db.client import db; print(db.list_collection_names())"
```

## Common Scenarios

### Daily Operations

1. **Morning Check**: `python -m app.cli.main show-due-leads`
2. **Start Processing**: `python -m app.cli.main run-dispatcher --verbose`
3. **Monitor Progress**: Watch logs for `worker.sent` and `worker.status_updated`

### Troubleshooting

1. **No emails sending**: Check `show-due-leads` and `list-accounts`
2. **Template errors**: Use `debug-template` command
3. **Lead stuck**: Use `reset-lead-progress` command

### After System Restart

1. **Check overdue leads**: `python -m app.cli.main show-due-leads`
2. **Resume processing**: `python -m app.cli.main run-dispatcher --verbose`
3. **Verify continuity**: System automatically resumes from exact state

## Key Log Messages

-   ✅ `worker.sent` - Email successfully sent
-   📧 `worker.status_updated` - Lead status changed to "contacted"
-   ⏰ `worker.recipient_processed` - Next recipient scheduled
-   🎯 `worker.step_completed` - All recipients done for current step
-   🔒 `arbiter.reserved` - Email account reserved
-   ❌ `worker.template_error` - Template rendering failed

## Environment Setup

```bash
# Create .env file
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=your_database_name
SMTP_STARTTLS=True
LOG_LEVEL=INFO

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Template Variables

### Most Common Variables:

-   `{{name}}` - Recipient's full name
-   `{{email}}` - Recipient's email
-   `{{first_name_me}}` - Sender's first name (from email_general_settings)
-   `{{last_name_me}}` - Sender's last name (from email_general_settings)
-   `{{account_signature}}` - Email signature

### Template Example:

```html
Hello {{name}}, Thanks for your interest! Best regards, {{first_name_me}}
{{last_name_me}} {{account_signature}}
```

## Quick Health Check

```bash
# Test everything is working
python -m app.cli.main show-due-leads
python -m app.cli.main list-campaigns
python -m app.cli.main list-accounts
python -m app.cli.main run-dispatcher --dry-run --verbose
```

---

_For complete documentation, see the main [README.md](README.md)_
