# Email Automation System - Running Without Docker

## Prerequisites

1. **Python 3.11+** installed on your system
2. **MongoDB Atlas** connection (already configured)
3. **Git** (optional, for version control)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

The `.env` file is already configured with your MongoDB Atlas connection:

```env
MONGO_URI=mongodb+srv://mandipredliodesigns:mandip@portalnew.uxjlc.mongodb.net/
DB_NAME=email_warmup
LOG_LEVEL=INFO
DISPATCHER_TICK_SECONDS=15
DEFAULT_WORKER_BATCH_SIZE=20
DEFAULT_RESERVATION_LOCK_SECONDS=30
SMTP_STARTTLS=true
DAY_BOUNDARY_TZ=UTC
```

### 3. Running the System

#### Option A: Interactive Menu (Recommended)

**Windows:**

```cmd
run.bat
```

**Linux/Mac:**

```bash
chmod +x run.sh
./run.sh
```

#### Option B: Direct Commands

**Run dispatcher once:**

```bash
python -m app.cli.main run-dispatcher --verbose
```

**Run continuously:**

```bash
python -m app.cli.main run-continuous
```

**Check account states:**

```bash
python -m app.cli.main check-runtime-states
```

**List campaigns:**

```bash
python -m app.cli.main list-campaigns
```

**List leads:**

```bash
python -m app.cli.main list-leads
```

## Available Commands

| Command                  | Description                                   |
| ------------------------ | --------------------------------------------- |
| `run-dispatcher`         | Run the dispatcher once                       |
| `run-continuous`         | Run dispatcher continuously (production mode) |
| `check-runtime-states`   | Check account runtime states                  |
| `fix-runtime-states`     | Fix problematic runtime states                |
| `list-campaigns`         | List all campaigns                            |
| `list-leads`             | List campaign leads                           |
| `ensure-indexes`         | Ensure database indexes                       |
| `backfill-lead-progress` | Backfill lead progress                        |
| `recount-runtime-states` | Recount runtime states                        |

## Production Deployment

For production, use the continuous mode:

```bash
python -m app.cli.main run-continuous --tick-seconds 60 --batch-size 50
```

Or create a systemd service (Linux) or Windows Service for automatic startup.

## System Architecture

-   **MongoDB Atlas**: Cloud database (already configured)
-   **Python Application**: Runs directly on your machine
-   **SMTP**: Uses account SMTP settings for email sending
-   **Logging**: Structured JSON logs to console/files
-   **CLI**: Management commands for operation

## No Docker Required!

This setup runs entirely on your local machine without any containers:

-   ✅ Direct Python execution
-   ✅ Cloud MongoDB (Atlas)
-   ✅ Local file logging
-   ✅ Environment variables from .env
-   ✅ All features working
