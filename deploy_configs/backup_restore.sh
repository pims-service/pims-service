#!/bin/bash
# ==============================================================================
# PIMS Database Backup & Restore Utility
# Runs on the server within the deployment directory
# ==============================================================================

set -e

# Make sure we are in the deployment root or docker-compose.yml directory
BACKUP_DIR="./backups"
DB_CONTAINER_NAME="psych_db"
DB_USER="psych_user"
DB_NAME="psych_db"

show_help() {
    echo "Usage: $0 [command] [args]"
    echo ""
    echo "Commands:"
    echo "  backup               Dump the database and save it as a compressed sql.gz file in $BACKUP_DIR/"
    echo "  restore [file.gz]    Restore the database using a compressed sql.gz backup file"
    echo "  help                 Show this help screen"
}

check_docker() {
    if ! docker compose ps | grep -q "$DB_CONTAINER_NAME"; then
        echo "ERROR: PostgreSQL database container '$DB_CONTAINER_NAME' is not running!"
        echo "Please ensure the container stack is online before executing backups or restores."
        exit 1
    fi
}

do_backup() {
    check_docker
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/pims_backup_$(date +%Y-%m-%d_%H%M%S).sql.gz"
    
    echo "=== Starting database backup ==="
    # Dump from the container database
    docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"
    
    echo "SUCCESS: Database dumped successfully!"
    echo "Backup location: $BACKUP_FILE"
    echo "File size: $(du -sh "$BACKUP_FILE" | cut -f1)"
}

do_restore() {
    RESTORE_FILE="$1"
    if [ -z "$RESTORE_FILE" ]; then
        echo "ERROR: Missing restore backup file parameter!"
        echo "Usage: $0 restore <path/to/backup_file.sql.gz>"
        exit 1
    fi

    if [ ! -f "$RESTORE_FILE" ]; then
        echo "ERROR: Backup file '$RESTORE_FILE' does not exist!"
        exit 1
    fi

    check_docker

    echo "WARNING: Restoring will overwrite existing data in database '$DB_NAME'."
    read -p "Are you sure you want to proceed with the restoration? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restoration cancelled."
        exit 0
    fi

    echo "=== Starting database restoration ==="
    # Terminate active connections to allow dropping/re-creating/writing without conflict
    echo "Terminating active database connections..."
    docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c \
        "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null

    # gunzip and execute inside target container
    echo "Injecting schema dump..."
    gunzip -c "$RESTORE_FILE" | docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME"

    echo "SUCCESS: Database restored successfully from '$RESTORE_FILE'!"
}

# Main routing logic
case "$1" in
    backup)
        do_backup
        ;;
    restore)
        do_restore "$2"
        ;;
    help|*)
        show_help
        ;;
esac
