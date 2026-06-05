#!/bin/bash
set -e
# RemediTrack Full Backup Script (DB + Media)

# 1. Configuration - Paths must be absolute for Cron
PROJECT_DIR="/home/ubuntu/Remeditrack-Devops"
ENV_FILE="$PROJECT_DIR/src/.env"
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# 2. Fetch configurations dynamically from .env
DB_HOST=$(grep '^DB_HOST=' $ENV_FILE | cut -d '=' -f2)
DB_USER=$(grep '^DB_USER=' $ENV_FILE | cut -d '=' -f2)
DB_NAME=$(grep '^DB_NAME=' $ENV_FILE | cut -d '=' -f2)
export PGPASSWORD=$(grep '^DB_PASSWORD=' $ENV_FILE | cut -d '=' -f2)
S3_BUCKET=$(grep '^AWS_BACKUP_BUCKET_NAME=' $ENV_FILE | cut -d '=' -f2)
AWS_REGION=$(grep '^AWS_S3_REGION_NAME=' $ENV_FILE | cut -d '=' -f2)

mkdir -p $BACKUP_DIR
echo "Backup Started: $TIMESTAMP"

# 3. Create Database Dump
FILENAME="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
echo "Dumping Database..."
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $FILENAME

# 4. Sync Media Files (Photos/Uploads)
echo "Syncing Media files to S3..."
aws s3 sync $PROJECT_DIR/src/media s3://$S3_BUCKET/media_backups/ --region $AWS_REGION

# 5. Upload Database Dump to S3
echo "Uploading DB dump to S3..."
aws s3 cp $FILENAME s3://$S3_BUCKET/db_backups/$(basename $FILENAME) --region $AWS_REGION

# 6. Cleanup
rm $FILENAME
echo "Backup Successful!"

