# Email Automation System

A production-ready, multi-campaign email automation system built with Python 3.11+ and MongoDB. This system provides comprehensive lead management, multi-recipient processing, account throttling, and real-time status tracking.

## 🎯 Features

### Core Functionality

-   **Multi-Campaign Management**: Handle multiple email campaigns simultaneously
-   **Multi-Recipient Processing**: Send emails to multiple recipients per lead with configurable timing
-   **Account Throttling**: Intelligent email account management with daily limits and wait times
-   **Real-time Status Tracking**: Track lead contact status in real-time as emails are sent
-   **Persistence**: Fully restart-safe with all state stored in MongoDB
-   **Template Engine**: Jinja2-based email templates with dynamic variable substitution
-   **Sequence Management**: Multi-step email sequences with customizable timing
-   **SMTP Integration**: Support for multiple SMTP providers (Gmail, Outlook, custom)

### Production Ready

-   **Docker-Free**: Runs in virtual environment without container dependencies
-   **Error Handling**: Comprehensive error handling with rollback capabilities
-   **Logging**: Structured logging with detailed operational insights
-   **CLI Management**: Full command-line interface for system administration
-   **MongoDB Cloud**: Cloud-based data persistence with automatic failover

## 📋 Requirements

-   Python 3.11+
-   MongoDB Atlas (cloud database)
-   SMTP accounts for sending emails
-   Virtual environment support

## 🚀 Installation

### 1. Clone and Setup Environment

```bash
# Clone the repository
cd "path/to/your/workspace"

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=your_database_name

# SMTP Configuration
SMTP_STARTTLS=True

# Logging
LOG_LEVEL=INFO
```

### 3. Database Setup

Ensure your MongoDB database has the following collections:

-   `campaigns` - Campaign definitions
-   `campaign_leads` - Lead data and progress tracking
-   `sequence_steps` - Email sequence step definitions
-   `templates` - Email templates
-   `email_accounts` - SMTP account configurations
-   `email_general_settings` - Account signatures and settings
-   `email_campaign_settings` - Account-specific campaign settings
-   `activities` - Email activity logs

## 🎮 Usage

### Basic Operations

#### Start the Email Dispatcher

```bash
# Run the main email processing dispatcher
python -m app.cli.main run-dispatcher --verbose

# Run in dry-run mode (no actual emails sent)
python -m app.cli.main run-dispatcher --dry-run --verbose
```

#### Lead Management

```bash
# View detailed lead information
python -m app.cli.main show-lead-details <lead_id>

# Show all leads currently due for processing
python -m app.cli.main show-due-leads

# Reset lead progress (clears all status and progress)
python -m app.cli.main reset-lead-progress <lead_id>

# Update lead statuses based on email activity
python -m app.cli.main update-lead-statuses
```

#### Campaign Management

```bash
# List all campaigns
python -m app.cli.main list-campaigns

# Show campaign details
python -m app.cli.main show-campaign <campaign_id>

# List email accounts
python -m app.cli.main list-accounts
```

#### Debug and Testing

```bash
# Debug template rendering
python -m app.cli.main debug-template <campaign_id> --lead-id <lead_id>

# Test SMTP connectivity
python -m app.cli.main test-smtp <account_id>
```

### Advanced Operations

#### Batch Processing

```bash
# Process specific campaign with custom batch size
python -m app.cli.main run-dispatcher --campaign-id <campaign_id> --batch-size 50

# Process with account filtering
python -m app.cli.main run-dispatcher --account-filter <account_id>
```

#### Status Management

```bash
# Bulk update lead statuses
python -m app.cli.main bulk-update-status --campaign-id <campaign_id> --status contacted

# Reset all campaign progress
python -m app.cli.main reset-campaign-progress <campaign_id>
```

## 🏗️ System Architecture

### Core Components

#### 1. Dispatcher (`app/domain/dispatcher.py`)

-   **Purpose**: Main orchestrator that manages campaign processing
-   **Functionality**:
    -   Discovers active campaigns
    -   Distributes work to workers
    -   Handles errors and retries
    -   Manages batch processing

#### 2. Worker (`app/domain/worker.py`)

-   **Purpose**: Processes individual leads and sends emails
-   **Functionality**:
    -   Multi-recipient processing with timing controls
    -   Template rendering and email composition
    -   Account selection and throttling
    -   Real-time status updates
    -   Progress tracking and sequence advancement

#### 3. Account Arbiter (`app/domain/arbiter.py`)

-   **Purpose**: Manages email account allocation and throttling
-   **Functionality**:
    -   Daily send limit enforcement
    -   Minimum wait time between sends
    -   Account reservation and locking
    -   Cross-campaign account sharing

#### 4. Template Engine (`app/domain/templating.py`)

-   **Purpose**: Handles email template rendering
-   **Functionality**:
    -   Jinja2 template processing
    -   Variable substitution with fallbacks
    -   HTML and text email generation
    -   Signature appending

### Data Models

#### Lead Data Structure

```python
{
  "_id": ObjectId("..."),
  "campaign_id": "campaign_id_string",
  "lead_data": [
    {
      "email": "user@example.com",
      "name": "User Name",
      "provider": "Google",
      "status": "contacted|not_contacted",
      "last_contacted_at": datetime,
      "last_step": 1,
      "first_name": "User",
      "last_name": "Name",
      "company_name": "Company Inc",
      "website": "https://example.com"
    }
  ],
  "progress": {
    "current_step_order": 1,
    "stopped": false,
    "last_sent_at": datetime,
    "next_due_at": datetime,
    "processed_recipients": {
      "step_1_recipient_0": {
        "processed_at": datetime,
        "email": "user@example.com",
        "template_id": "template_id"
      }
    }
  }
}
```

#### Campaign Configuration

```python
{
  "_id": ObjectId("..."),
  "name": "Campaign Name",
  "status": "active|paused|completed",
  "created_at": datetime,
  "sequence_id": "sequence_id_string",
  "settings": {
    "daily_limit": 50,
    "min_wait_time": 4,  # minutes between emails
    "batch_size": 20
  }
}
```

## 🔧 Configuration

### Email Account Setup

Email accounts are configured in the `email_accounts` collection:

```python
{
  "_id": ObjectId("..."),
  "email": "sender@example.com",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "sender@example.com",
  "smtp_password": "app_password",
  "status": "active",
  "provider": "Gmail"
}
```

### Campaign Settings

Configure per-account campaign settings in `email_campaign_settings`:

```python
{
  "_id": ObjectId("..."),
  "email_id": "account_object_id",
  "daily_limit": 50,
  "min_wait_time": 4,  # minutes
  "max_daily_sends": 100
}
```

### Email Templates

Templates use Jinja2 syntax with available variables:

```html
Subject: {{subject_line | default("Default Subject")}} Hello {{first_name |
default("there")}}, This is an email from {{sender_name}} at {{company_name |
default("our company")}}. Visit our website: {{website |
default("https://example.com")}} Best regards, {{account_signature}}
```

**Available Template Variables:**

-   `first_name`, `last_name`, `name` - Recipient information
-   `email` - Recipient email address
-   `company_name`, `website` - Company information
-   `sender_name`, `sender_first_name`, `sender_last_name` - Sender information
-   `sender_email` - Sender email address
-   `account_signature` - Account signature
-   `campaign_id`, `step_order` - Campaign context
-   Custom fields from lead data

## 📊 Monitoring and Logging

### Log Levels and Output

The system uses structured logging with the following levels:

-   **DEBUG**: Detailed operational information
-   **INFO**: General operational messages
-   **WARNING**: Warning conditions
-   **ERROR**: Error conditions

### Key Log Events

```bash
# Email sending
worker.sent - Email successfully sent
worker.status_updated - Lead status changed
worker.recipient_processed - Recipient processed with timing info
worker.step_completed - Email sequence step completed

# Account management
arbiter.reserved - Email account reserved
arbiter.committed - Account reservation committed
arbiter.rollback - Account reservation rolled back

# Errors
worker.template_error - Template rendering failed
worker.smtp_error - Email sending failed
worker.account_error - Account configuration issue
```

### Monitoring Commands

```bash
# Real-time processing status
python -m app.cli.main run-dispatcher --verbose

# Lead status overview
python -m app.cli.main show-due-leads

# Account usage stats
python -m app.cli.main show-account-stats

# Campaign progress
python -m app.cli.main show-campaign-progress <campaign_id>
```

## 🔄 Multi-Recipient Processing

### How It Works

The system intelligently handles multiple recipients per lead:

1. **Sequential Processing**: Recipients are processed one at a time
2. **Timing Control**: Configurable wait time between recipient emails
3. **Individual Tracking**: Each recipient has independent status tracking
4. **Step Coordination**: All recipients must complete a step before advancing

### Configuration

```python
# Campaign settings for multi-recipient timing
{
  "min_wait_time": 4,  # Minutes between recipients
  "batch_size": 20,    # Leads processed per batch
  "daily_limit": 50    # Emails per account per day
}
```

### Processing Flow

```
Lead with 3 recipients:
├── Recipient 1: Email sent → Status: contacted → Wait 4 minutes
├── Recipient 2: Email sent → Status: contacted → Wait 4 minutes
├── Recipient 3: Email sent → Status: contacted → Step completed
└── All recipients done → Advance to next step
```

## 🛡️ Error Handling

### Automatic Recovery

-   **SMTP Failures**: Automatic account rollback and retry with different account
-   **Template Errors**: Detailed error logging with variable context
-   **Database Issues**: Connection retry with exponential backoff
-   **Account Limits**: Automatic account switching when limits reached

### Manual Recovery

```bash
# Reset problematic lead
python -m app.cli.main reset-lead-progress <lead_id>

# Force account availability
python -m app.cli.main reset-account-limits <account_id>

# Rebuild lead status
python -m app.cli.main update-lead-statuses
```

## 📈 Performance Optimization

### Batch Processing

-   Configurable batch sizes (default: 20 leads)
-   Parallel campaign processing
-   Efficient MongoDB queries with proper indexing

### Account Management

-   Round-robin account selection
-   Intelligent throttling to prevent rate limiting
-   Account health monitoring

### Memory Management

-   Streaming lead processing
-   Minimal memory footprint
-   Efficient template caching

## 🔒 Security

### SMTP Security

-   TLS/STARTTLS encryption support
-   Secure credential storage
-   App-specific passwords recommended

### Database Security

-   MongoDB Atlas with encryption at rest
-   Connection string security
-   Environment variable configuration

### Access Control

-   CLI-based administration
-   No web interface by default
-   Audit logging for all operations

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:

    ```bash
    # Production environment
    export ENV=production
    export LOG_LEVEL=INFO
    export MONGO_URI="mongodb+srv://..."
    ```

2. **Service Management**:

    ```bash
    # Run as system service (systemd example)
    [Unit]
    Description=Email Automation Dispatcher
    After=network.target

    [Service]
    Type=simple
    User=emailbot
    WorkingDirectory=/opt/email-automation
    ExecStart=/opt/email-automation/.venv/bin/python -m app.cli.main run-dispatcher
    Restart=always
    RestartSec=30

    [Install]
    WantedBy=multi-user.target
    ```

3. **Monitoring**:
    ```bash
    # Health check script
    #!/bin/bash
    python -m app.cli.main show-due-leads | grep -q "Found"
    if [ $? -eq 0 ]; then
      echo "System healthy"
    else
      echo "System needs attention"
    fi
    ```

### Scaling Considerations

-   **Horizontal Scaling**: Run multiple dispatcher instances
-   **Database Indexing**: Ensure proper MongoDB indexes
-   **Account Distribution**: Distribute SMTP accounts across instances
-   **Rate Limiting**: Monitor and adjust daily limits

## 🐛 Troubleshooting

### Common Issues

#### 1. No Emails Being Sent

```bash
# Check due leads
python -m app.cli.main show-due-leads

# Check account status
python -m app.cli.main list-accounts

# Test SMTP connectivity
python -m app.cli.main test-smtp <account_id>
```

#### 2. Template Errors

```bash
# Debug template rendering
python -m app.cli.main debug-template <campaign_id> --lead-id <lead_id>

# Check available variables
python -m app.cli.main show-lead-details <lead_id>
```

#### 3. Account Throttling

```bash
# Check account limits
python -m app.cli.main show-account-stats

# Reset account if needed
python -m app.cli.main reset-account-limits <account_id>
```

#### 4. Database Connection Issues

```bash
# Test database connectivity
python -c "from app.db.client import db; print(db.list_collection_names())"

# Check environment variables
echo $MONGO_URI
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Maximum verbosity
python -m app.cli.main run-dispatcher --verbose --dry-run

# Debug specific lead
python -m app.cli.main debug-template <campaign_id> --lead-id <lead_id>

# Check system state
python -m app.cli.main show-due-leads
python -m app.cli.main list-campaigns
python -m app.cli.main list-accounts
```

## 📚 API Reference

### CLI Commands

| Command                | Description                   | Parameters                                                |
| ---------------------- | ----------------------------- | --------------------------------------------------------- |
| `run-dispatcher`       | Start email processing        | `--verbose`, `--dry-run`, `--campaign-id`, `--batch-size` |
| `show-lead-details`    | Show lead information         | `<lead_id>`                                               |
| `show-due-leads`       | List leads due for processing | None                                                      |
| `reset-lead-progress`  | Reset lead progress           | `<lead_id>`                                               |
| `update-lead-statuses` | Update lead statuses          | None                                                      |
| `list-campaigns`       | List all campaigns            | None                                                      |
| `list-accounts`        | List email accounts           | None                                                      |
| `debug-template`       | Debug template rendering      | `<campaign_id>`, `--lead-id`                              |

### Environment Variables

| Variable        | Description               | Default  |
| --------------- | ------------------------- | -------- |
| `MONGO_URI`     | MongoDB connection string | Required |
| `DB_NAME`       | Database name             | Required |
| `SMTP_STARTTLS` | Enable STARTTLS           | `True`   |
| `LOG_LEVEL`     | Logging level             | `INFO`   |

## 🔄 System Persistence

### Restart Safety

The system is designed to be fully restart-safe:

-   **All state stored in MongoDB**: No local state files
-   **Exact timing preservation**: Next due timestamps maintained
-   **Progress tracking**: Each recipient and step tracked individually
-   **Account state**: Throttling and limits persist across restarts

### Shutdown and Restart Process

1. **Shutdown**: System can be safely stopped at any time
2. **State Preservation**: All progress saved to MongoDB
3. **Restart**: System automatically resumes from exact point
4. **Recovery**: Overdue leads are processed immediately

Example restart scenario:

```bash
# Stop system (Ctrl+C or system shutdown)
# ... hours/days later ...

# Restart system
python -m app.cli.main run-dispatcher --verbose

# System automatically:
# 1. Finds overdue leads
# 2. Resumes multi-recipient processing
# 3. Continues sequence steps
# 4. Maintains all throttling
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `python -m pytest`
5. Submit a pull request

### Code Style

-   Follow PEP 8 guidelines
-   Use type hints where appropriate
-   Add docstrings for public functions
-   Include error handling and logging

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check this README for common solutions
2. Review the troubleshooting section
3. Check system logs for error details
4. Use debug commands to investigate issues

## 📊 System Status

The system maintains full persistence across restarts and provides:

-   ✅ **Real-time status tracking**
-   ✅ **Multi-recipient processing**
-   ✅ **Account throttling**
-   ✅ **Template rendering**
-   ✅ **Error recovery**
-   ✅ **Production deployment**
-   ✅ **MongoDB persistence**
-   ✅ **CLI management interface**

**Ready for production use with comprehensive email automation capabilities!** 🚀
