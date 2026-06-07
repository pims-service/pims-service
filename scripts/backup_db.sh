#!/bin/bash
# Clean and optimized database backup script for psychological experiment platform.

set -e

# Configuration
BACKUP_DIR="/home/sj/db_backups"
KEEP_DAYS=30
DB_CONTAINER="psych_db"
DB_USER="psych_user"
DB_NAME="psych_db"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

echo "[$TIMESTAMP] Starting database backup..."

# Perform pg_dump inside the docker container, compress it, and save to host
if docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    echo "[$TIMESTAMP] Backup successful: $BACKUP_FILE"
    echo "[$TIMESTAMP] Size: $(du -sh "$BACKUP_FILE" | cut -f1)"
else
    echo "[$TIMESTAMP] Error: Database backup failed!" >&2
    exit 1
fi

# Clean up backups older than $KEEP_DAYS
echo "[$TIMESTAMP] Cleaning up backups older than $KEEP_DAYS days..."
find "$BACKUP_DIR" -type f -name "db_backup_*.sql.gz" -mtime +"$KEEP_DAYS" -delete
echo "[$TIMESTAMP] Cleanup finished."
