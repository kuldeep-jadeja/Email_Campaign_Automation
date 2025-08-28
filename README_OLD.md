# EmailBot

Multi-campaign email automation system with MongoDB, per-campaign schedules, per-account throttles, and cross-campaign account sharing.

## Quick Setup

1. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2. **Set up environment:**

    ```bash
    cp .env.example .env
    # Edit .env with your MongoDB URI and other settings
    ```

3. **Start MongoDB (if using Docker):**

    ```bash
    docker-compose up mongo -d
    ```

4. **Initialize indexes:**
    ```bash
    python -m app.cli.main init-indexes
    ```

## Database Setup

Your campaign queue needs to reference actual campaign IDs. Update campaign_queue:

```javascript
// In MongoDB shell
db.campaign_queue.updateOne(
    { campaign_id: "old_id" },
    { $set: { campaign_id: "actual_campaign_id" } },
);
```

Make sure your campaigns have `status: "active"` to be processed by dispatcher.

## Running the System

### 1. Run Dispatcher (global scheduler)

```bash
python -m app.cli.main run-dispatcher --batch-size 20 --verbose
```

### 2. Run Continuous Dispatcher

```bash
python -m app.cli.main continuous-dispatcher --tick-seconds 15 --batch-size 20 --verbose
```

### 3. Run Worker for Specific Campaign

```bash
python -m app.cli.main run-worker --campaign <campaign_id> --batch-size 10 --dry-run
```

### 4. Backfill Lead Progress

```bash
python -m app.cli.main backfill-progress --campaign <campaign_id>
```

### 5. List Email Accounts

```bash
python -m app.cli.main list-accounts
```

### 6. Recount Runtime State

```bash
python -m app.cli.main recount-runtime --email-id <email_id> --date 2025-08-27
```

## Data Requirements

Ensure your database has:

1. **Active campaigns** with `status: "active"`
2. **Campaign queue** with valid campaign IDs
3. **Campaign schedules** with proper timezone format
4. **Campaign sequences** with step arrays containing `id` and `order`
5. **Sequence steps** with `active_template` field
6. **Templates** with `subject` and `content` fields
7. **Email accounts** with SMTP credentials
8. **Email campaign settings** with `daily_limit` and `min_wait_time`
9. **Leads** with `lead_data` containing `email` field

## Schema Notes

-   Lead data can be array or object (worker handles both)
-   Templates use `content` field for HTML body
-   Email accounts use both `smtp_passcode` and `smtp_password`
-   Schedules use `scheduled_days` array
-   All dates stored in UTC

## Testing

```bash
pytest
```

## Configuration

Environment variables in `.env`:

-   `MONGO_URI`: MongoDB connection string
-   `DB_NAME`: Database name
-   `SMTP_STARTTLS`: Enable SMTP STARTTLS
-   `LOG_LEVEL`: Logging level (INFO/DEBUG)

## Logging

JSON structured logs with correlation IDs including:

-   campaign_id, email_id, lead_id
-   step_order, template_id
-   Error reasons and success metrics

-   Code style: black, ruff, mypy
-   Tests: pytest, freezegun, mongomock
-   Container: Docker + docker-compose
