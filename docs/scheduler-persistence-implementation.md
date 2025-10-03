# APScheduler PostgreSQL Persistence Implementation

## Overview

This document describes the implementation of PostgreSQL-based persistence for APScheduler in the OpenLearn platform, enabling job recovery across application restarts and ensuring reliable scheduled scraping operations.

## Architecture

### Components

1. **Database Manager** (`app/core/scheduler_db.py`)
   - Connection management
   - Table initialization
   - Health checks
   - Job cleanup

2. **Scheduler Service** (`app/services/scheduler.py`)
   - APScheduler integration
   - Job lifecycle management
   - Event monitoring

3. **Configuration** (`app/config/scheduler_config.py`)
   - PostgreSQL jobstore setup
   - Executor configuration
   - Job defaults

4. **Settings** (`app/config/settings.py`)
   - Database URLs (async and sync)
   - Connection parameters

## Key Features

### 1. PostgreSQL Persistence

Jobs are stored in the `apscheduler_jobs` table using SQLAlchemy's synchronous driver (psycopg2):

```python
JOBSTORES = {
    'default': SQLAlchemyJobStore(
        url=settings.DATABASE_URL_SYNC,
        tablename='apscheduler_jobs'
    )
}
```

### 2. Automatic Job Recovery

When the scheduler starts:
- Validates database connection
- Checks table existence
- Recovers persisted jobs from PostgreSQL
- Resumes scheduled operations

### 3. Connection Management

**Dual Database URLs:**
- `DATABASE_URL`: Async URL for FastAPI/SQLAlchemy async operations (asyncpg)
- `DATABASE_URL_SYNC`: Sync URL for APScheduler (psycopg2)

**Connection Pooling:**
- Pool size: 5 connections
- Max overflow: 10 connections
- Pool recycle: 1 hour
- Pre-ping validation

### 4. Health Monitoring

Comprehensive health checks include:
- Database connection validation
- Table existence verification
- Job count tracking
- Error detection

## Database Schema

APScheduler automatically creates the following table:

```sql
CREATE TABLE apscheduler_jobs (
    id VARCHAR(191) PRIMARY KEY,
    next_run_time FLOAT,
    job_state BYTEA NOT NULL
);

CREATE INDEX ix_apscheduler_jobs_next_run_time
ON apscheduler_jobs (next_run_time);
```

## Usage

### Initialize Database

Run the initialization script:

```bash
cd backend
python scripts/init_scheduler_db.py
```

This will:
- Validate PostgreSQL connection
- Check/create tables
- Display health status

### Scheduler Lifecycle

```python
from app.services.scheduler import get_scheduler_service

# Get scheduler instance
scheduler = get_scheduler_service()

# Start scheduler (automatically connects to PostgreSQL)
await scheduler.start()

# Jobs are automatically persisted
# ...

# Shutdown gracefully (jobs remain in database)
await scheduler.shutdown(wait=True)
```

### Manual Job Management

```python
# Add a job
scheduler.scheduler.add_job(
    func=my_function,
    trigger='interval',
    minutes=30,
    id='unique_job_id',
    replace_existing=True
)

# Pause a job
scheduler.pause_job('unique_job_id')

# Resume a job
scheduler.resume_job('unique_job_id')

# Get job details
job_info = scheduler.get_job('unique_job_id')
```

### Health Checks

```python
from app.core.scheduler_db import scheduler_db_health_check

# Check database health
health = scheduler_db_health_check()

# Returns:
# {
#     'connection_valid': True,
#     'table_exists': True,
#     'job_count': 15,
#     'error': None
# }
```

### Job Cleanup

Old completed jobs are automatically cleaned up:

```python
from app.core.scheduler_db import cleanup_scheduler_database

# Clean up jobs completed more than 30 days ago
deleted = cleanup_scheduler_database(days=30)
print(f"Deleted {deleted} old jobs")
```

## Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=openlearn
POSTGRES_PASSWORD=openlearn123
POSTGRES_DB=openlearn

# Scheduler Configuration
MAX_CONCURRENT_SCRAPERS=5
ENABLE_SCHEDULER=True
```

### Scheduler Settings

**Job Defaults:**
- `coalesce`: True (combine missed runs)
- `max_instances`: 1 (prevent concurrent execution)
- `misfire_grace_time`: 300 seconds
- `replace_existing`: True (update on restart)

**Executors:**
- Thread pool: 5 workers (I/O bound scraping)
- Process pool: 2 workers (CPU intensive tasks)

## Error Handling

### Startup Errors

```python
try:
    await scheduler.start()
except RuntimeError as e:
    if "database" in str(e).lower():
        # Database connection failed
        # Check PostgreSQL is running
        # Verify credentials
```

### Connection Validation

The scheduler validates database connection before starting:

```python
# Automatic validation in scheduler.start()
db_initialized = initialize_scheduler_database()
if not db_initialized:
    raise RuntimeError("Failed to initialize database")

health_status = scheduler_db_health_check()
if not health_status['connection_valid']:
    raise RuntimeError("Database connection invalid")
```

## Testing

Run persistence tests:

```bash
# Unit tests
pytest backend/tests/services/test_scheduler_persistence.py -v

# Integration tests
pytest backend/tests/services/test_scheduler_persistence.py -v -m integration
```

### Test Coverage

- Database manager singleton pattern
- Connection validation
- Table initialization
- Job persistence across restarts
- Concurrent access
- Error handling
- Cleanup operations

## Monitoring

### Metrics

The scheduler tracks:
- Jobs executed
- Jobs failed
- Jobs missed
- Last execution time
- Uptime

Access via:

```bash
GET /api/v1/scheduler/metrics
```

### Status Endpoint

```bash
GET /api/v1/scheduler/status
```

Returns:
```json
{
  "status": "running",
  "running": true,
  "total_jobs": 15,
  "metrics": {
    "jobs_executed": 234,
    "jobs_failed": 3,
    "jobs_missed": 0,
    "uptime_seconds": 86400
  },
  "jobs": [...]
}
```

## Migration Steps

### For Existing Deployments

1. **Backup Current Jobs** (if any in-memory jobs):
   ```python
   jobs = scheduler.scheduler.get_jobs()
   # Save job configurations
   ```

2. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   ```bash
   python scripts/init_scheduler_db.py
   ```

4. **Restart Application**:
   - Scheduler will automatically use PostgreSQL
   - Jobs will persist across restarts

5. **Verify Persistence**:
   ```bash
   # Check health
   curl http://localhost:8000/api/v1/scheduler/health

   # View jobs
   curl http://localhost:8000/api/v1/scheduler/jobs
   ```

## Troubleshooting

### Issue: "Database connection validation failed"

**Solution:**
- Verify PostgreSQL is running
- Check `POSTGRES_*` environment variables
- Test connection: `psql -h localhost -U openlearn -d openlearn`

### Issue: "Table does not exist"

**Solution:**
- Run initialization script: `python scripts/init_scheduler_db.py`
- APScheduler creates table automatically on first start

### Issue: "Jobs not persisting"

**Solution:**
- Check `DATABASE_URL_SYNC` is using `psycopg2` driver
- Verify jobstore configuration in `scheduler_config.py`
- Check database write permissions

### Issue: "Too many database connections"

**Solution:**
- Reduce `DB_POOL_SIZE` in settings
- Check for connection leaks
- Ensure `scheduler.shutdown()` is called properly

## Performance Considerations

### Connection Pooling

- Default pool size: 5 connections
- Suitable for most deployments
- Increase for high-concurrency scenarios

### Job Storage

- Jobs stored as binary (pickled) Python objects
- Minimal storage overhead
- Indexes on `next_run_time` for fast queries

### Cleanup

- Automatic cleanup of old jobs (30 day retention)
- Runs daily at configured time
- Prevents database bloat

## Security

### Database Access

- Use strong passwords
- Limit database user permissions
- Use SSL for production connections

### Job Data

- Jobs may contain sensitive data
- Consider encryption for job_state column
- Implement access controls

## Future Enhancements

1. **Job History**
   - Track execution history
   - Store results and errors
   - Analytics dashboard

2. **Distributed Scheduling**
   - Multi-instance coordination
   - Leader election
   - Load balancing

3. **Advanced Monitoring**
   - Real-time job tracking
   - Performance metrics
   - Alerting on failures

4. **Job Templates**
   - Predefined job configurations
   - Dynamic job creation
   - Version control

## References

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Support

For issues or questions:
- Check logs: `backend/logs/scheduler.log`
- Review test suite: `backend/tests/services/test_scheduler_persistence.py`
- Database health check: `python scripts/init_scheduler_db.py`
