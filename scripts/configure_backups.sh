#!/bin/bash
# RemediTrack Backup Configuration & Scheduler
set -e


echo "Configuring Automated Backups..."

# 1. Install prerequisites
echo "Installing PostgreSQL 16 Client and AWS CLI..."
sudo apt update
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
sudo apt update
sudo apt install -y postgresql-client-16 awscli

# 2. Setup Environment Variables
ENV_FILE="/home/ubuntu/Remeditrack-Devops/src/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Ask for bucket name if not already in .env
if ! grep -q "AWS_BACKUP_BUCKET_NAME" "$ENV_FILE"; then
    read -p "Enter your S3 Backup Bucket Name (e.g. remeditrack-backups-xxx): " BUCKET_NAME
    echo "AWS_BACKUP_BUCKET_NAME=$BUCKET_NAME" >> "$ENV_FILE"
    echo "Added bucket name to .env"
fi

# 3. Fix Permissions
chmod +x /home/ubuntu/Remeditrack-Devops/scripts/backup_db.sh

# 4. Schedule Cron Job (2:00 AM Daily)
SCRIPT_PATH="/home/ubuntu/Remeditrack-Devops/scripts/backup_db.sh"
LOG_PATH="/home/ubuntu/backup_cron.log"
CRON_JOB="0 2 * * * $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Add to crontab if not already there
(crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH") || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Configuration Complete!"
echo "Backup scheduled daily at 2:00 AM."
echo "Log file: $LOG_PATH"

