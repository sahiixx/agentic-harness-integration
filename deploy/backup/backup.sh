#!/bin/bash
# SAHIIX Production Backup Script
# Runs daily via cron in backup container

set -euo pipefail

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Database backup
echo "[$(date)] Starting PostgreSQL backup..."
pg_dump -h postgres -U sahiix -d sahiix | gzip > "${BACKUP_DIR}/sahiix_db_${DATE}.sql.gz"

# Config backup
echo "[$(date)] Backing up configs..."
tar -czf "${BACKUP_DIR}/sahiix_configs_${DATE}.tar.gz" \
    /root/agentic-harness-integration/deploy \
    /root/.hermes/config.json \
    /root/.hermes/config.yaml 2>/dev/null || true

# Ollama models backup (metadata only)
echo "[$(date)] Backing up Ollama model list..."
curl -s http://ollama:11434/api/tags | jq . > "${BACKUP_DIR}/ollama_models_${DATE}.json"

# Cleanup old backups
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -delete

# Upload to S3 if configured
if [[ -n "${S3_ENDPOINT}" && -n "${S3_BUCKET}" ]]; then
    echo "[$(date)] Uploading to S3..."
    for file in "${BACKUP_DIR}"/*_${DATE}.*; do
        if [[ -f "$file" ]]; then
            aws --endpoint-url "${S3_ENDPOINT}" s3 cp "$file" "s3://${S3_BUCKET}/sahiix/$(basename "$file")" || echo "S3 upload failed for $file"
        fi
    done
fi

echo "[$(date)] Backup completed successfully."