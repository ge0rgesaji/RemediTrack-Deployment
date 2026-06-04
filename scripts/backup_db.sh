#!/bin/bash
set -e
# RemediTrack Database Backup Script - Dynamic Version

# Path to your environment file
ENV_FILE="/home/ubuntu/RemediTrack-Deployment/src/.env"

# 1. Fetch configurations dynamically from .env
DB_HOST=$(grep '^DB_HOST=' $ENV_FILE | cut -d '=' -f2)
DB_USER=$(grep '^DB_USER=' $ENV_FILE | cut -d '=' -f2)
DB_NAME=$(grep '^DB_NAME=' $ENV_FILE | cut -d '=' -f2)
export PGPASSWORD=$(grep '^DB_PASSWORD=' $ENV_FILE | cut -d '=' -f2)
S3_BUCKET=$(grep '^AWS_BACKUP_BUCKET_NAME=' $ENV_FILE | cut -d '=' -f2)
AWS_REGION=$(grep '^AWS_S3_REGION_NAME=' $ENV_FILE | cut -d '=' -f2)

# 2. Local Setup
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
mkdir -p $BACKUP_DIR
FILENAME="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

echo "------------------------------------------------"
echo "🗄️  Starting backup for $DB_NAME..."
echo "📍 Destination Bucket: $S3_BUCKET"
echo "------------------------------------------------"

# 3. Create Database Dump
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $FILENAME

# 4. Upload to the Private S3 Bucket
aws s3 cp $FILENAME s3://$S3_BUCKET/backups/$(basename $FILENAME) --region $AWS_REGION

# 5. Cleanup
rm $FILENAME
echo "✅ Backup complete and uploaded to S3!"
