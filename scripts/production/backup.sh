#!/bin/bash
# ============================================================================
# OpenLearn Colombia - Automated Backup Script
# ============================================================================
# Backs up PostgreSQL database and important files
# Runs daily at 2am via cron job
# Retains backups for 30 days
# ============================================================================

set -e

# Configuration
BACKUP_DIR="/backups/openlearn"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
KEEP_DAYS=30
PROJECT_DIR="/opt/open_learn"

# Logging
log_file="/var/log/openlearn-backup.log"

echo "[$(date)] Starting backup..." | tee -a "$log_file"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

# ============================================================================
# Backup Database
# ============================================================================

echo "[$(date)] Backing up PostgreSQL database..." | tee -a "$log_file"

# Get database credentials from .env
DB_USER=$(grep "^POSTGRES_USER=" .env | cut -d'=' -f2)
DB_NAME=$(grep "^POSTGRES_DB=" .env | cut -d'=' -f2)

# Backup database
docker-compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

DB_BACKUP_SIZE=$(du -h "$BACKUP_DIR/db_backup_$DATE.sql.gz" | cut -f1)
echo "[$(date)] Database backup created: db_backup_$DATE.sql.gz ($DB_BACKUP_SIZE)" | tee -a "$log_file"

# ============================================================================
# Backup Uploaded Files (when avatar upload is implemented)
# ============================================================================

# Uncomment when file upload is added:
# if docker volume ls | grep -q "openlearn_uploads"; then
#     echo "[$(date)] Backing up uploaded files..." | tee -a "$log_file"
#     docker run --rm -v openlearn_uploads:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads_$DATE.tar.gz -C /data .
#     UPLOAD_BACKUP_SIZE=$(du -h "$BACKUP_DIR/uploads_$DATE.tar.gz" | cut -f1)
#     echo "[$(date)] Uploads backup created: uploads_$DATE.tar.gz ($UPLOAD_BACKUP_SIZE)" | tee -a "$log_file"
# fi

# ============================================================================
# Backup Configuration Files
# ============================================================================

echo "[$(date)] Backing up configuration..." | tee -a "$log_file"

# Backup .env (contains secrets - store securely!)
cp .env "$BACKUP_DIR/env_backup_$DATE.txt"
chmod 600 "$BACKUP_DIR/env_backup_$DATE.txt"

# Backup docker-compose configuration
cp docker-compose.yml "$BACKUP_DIR/docker-compose_backup_$DATE.yml" 2>/dev/null || true

echo "[$(date)] Configuration backed up" | tee -a "$log_file"

# ============================================================================
# Cleanup Old Backups
# ============================================================================

echo "[$(date)] Cleaning up old backups (older than $KEEP_DAYS days)..." | tee -a "$log_file"

# Delete old database backups
OLD_DB_COUNT=$(find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$KEEP_DAYS | wc -l)
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete

# Delete old upload backups
OLD_UPLOAD_COUNT=$(find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$KEEP_DAYS 2>/dev/null | wc -l || echo 0)
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$KEEP_DAYS -delete 2>/dev/null || true

# Delete old config backups
OLD_CONFIG_COUNT=$(find "$BACKUP_DIR" -name "env_backup_*.txt" -mtime +$KEEP_DAYS | wc -l)
find "$BACKUP_DIR" -name "env_backup_*.txt" -mtime +$KEEP_DAYS -delete

echo "[$(date)] Deleted $OLD_DB_COUNT old database backups" | tee -a "$log_file"
echo "[$(date)] Deleted $OLD_CONFIG_COUNT old config backups" | tee -a "$log_file"

# ============================================================================
# Backup Summary
# ============================================================================

TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo "" | tee -a "$log_file"
echo "╔══════════════════════════════════════════╗" | tee -a "$log_file"
echo "║  Backup Complete                         ║" | tee -a "$log_file"
echo "╚══════════════════════════════════════════╝" | tee -a "$log_file"
echo "Date: $DATE" | tee -a "$log_file"
echo "Database backup: db_backup_$DATE.sql.gz ($DB_BACKUP_SIZE)" | tee -a "$log_file"
echo "Total backups: $TOTAL_BACKUPS files ($TOTAL_SIZE)" | tee -a "$log_file"
echo "Retention: $KEEP_DAYS days" | tee -a "$log_file"
echo "" | tee -a "$log_file"

# Optional: Send notification email about backup status
# Uncomment when email service is configured:
# echo "Backup completed at $DATE" | mail -s "OpenLearn Backup Success" admin@openlearn.co

exit 0
