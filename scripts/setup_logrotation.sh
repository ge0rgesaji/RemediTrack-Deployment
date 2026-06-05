#!/bin/bash
# RemediTrack Log Rotation Automation Script
set -e

echo "Configuring Professional Log Rotation..."

# 1. Configure Docker Global Log Limits
# This prevents Docker logs from ever exceeding 10MB per file
echo "Setting Docker global log limits..."
sudo bash -c 'cat <<EOF > /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF'

echo "Restarting Docker to apply limits..."
sudo systemctl restart docker

# 2. Configure logrotate for Docker Container Files
# This handles the physical .log files on the disk
echo "Configuring logrotate for Docker containers..."
sudo bash -c 'cat <<EOF > /etc/logrotate.d/docker-containers
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
EOF'

# 3. Configure logrotate for App Backup Logs
echo "Configuring logrotate for RemediTrack backup logs..."
sudo bash -c 'cat <<EOF > /etc/logrotate.d/remeditrack-backups
/home/ubuntu/backup_cron.log {
    rotate 5
    weekly
    compress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
}
EOF'

# 4. Verify Nginx logrotate exists
if [ -f /etc/logrotate.d/nginx ]; then
    echo "Nginx logrotation is already present."
else
    echo "Warning: Nginx logrotation config not found. Nginx might need re-installation."
fi

# 5. Test the configurations
echo "Testing logrotate syntax..."
sudo logrotate -d /etc/logrotate.d/docker-containers
sudo logrotate -d /etc/logrotate.d/remeditrack-backups


echo "Log Rotation Automation Complete!"

