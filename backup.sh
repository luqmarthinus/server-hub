#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default paths
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment variables from .env if present
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Ensure MySQL root password is set
if [ -z "${MYSQL_ROOT_PASSWORD:-}" ]; then
    echo "ERROR: MYSQL_ROOT_PASSWORD not set in .env or environment."
    exit 1
fi

# Ensure the MySQL container is running
if ! docker compose ps --status running | grep -q mysql; then
    echo "ERROR: MySQL container is not running. Start the stack with 'docker compose up -d' first."
    exit 1
fi

usage() {
    cat << EOF
Usage: $0 {backup|restore|list} [filename]

Commands:
  backup                     Create a timestamped backup in ${BACKUP_DIR}
  restore <filename.sql>     Restore database from the given SQL file
  list                       List available backup files in ${BACKUP_DIR}
EOF
    exit 1
}

mkdir -p "$BACKUP_DIR"

backup() {
    local backup_file="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"
    echo "Creating backup: $backup_file"
    docker compose exec -T mysql mysqldump \
        -u root -p"${MYSQL_ROOT_PASSWORD}" \
        --single-transaction --routines --triggers \
        "${MYSQL_DATABASE:-server_hub_db}" > "$backup_file"
    if [ $? -eq 0 ]; then
        echo "Backup completed successfully."
        echo "File: $backup_file"
    else
        echo "ERROR: Backup failed."
        exit 1
    fi
}

restore() {
    local restore_file="$1"
    if [ ! -f "$restore_file" ]; then
        echo "ERROR: File not found: $restore_file"
        exit 1
    fi
    echo "WARNING: This will overwrite the current database. All existing data will be lost."
    read -p "Are you sure? Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled."
        exit 0
    fi
    echo "Restoring from $restore_file ..."
    # Drop and recreate the database to ensure clean state
    docker compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
        -e "DROP DATABASE IF EXISTS ${MYSQL_DATABASE:-server_hub_db}; CREATE DATABASE ${MYSQL_DATABASE:-server_hub_db};"
    cat "$restore_file" | docker compose exec -T mysql \
        mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE:-server_hub_db}"
    if [ $? -eq 0 ]; then
        echo "Restore completed successfully."
    else
        echo "ERROR: Restore failed."
        exit 1
    fi
}

list_backups() {
    if [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        echo "No backups found in $BACKUP_DIR"
    else
        echo "Available backups in $BACKUP_DIR:"
        ls -1 "$BACKUP_DIR" | grep '\.sql$' | sort -r
    fi
}

case "${1:-}" in
    backup)
        backup
        ;;
    restore)
        if [ $# -ne 2 ]; then
            echo "ERROR: restore requires a filename argument."
            usage
        fi
        restore "$2"
        ;;
    list)
        list_backups
        ;;
    *)
        usage
        ;;
esac