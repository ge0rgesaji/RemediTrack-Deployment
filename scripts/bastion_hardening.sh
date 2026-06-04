#!/bin/bash
set -e

echo "------------------------------------------------"
echo "🔒 Starting AGGRESSIVE BASTION HARDENING..."
echo "------------------------------------------------"

# 1. Update and install security tools
sudo apt update
sudo apt install -y fail2ban unattended-upgrades

# 2. Aggressive Fail2Ban Configuration
# Lower maxretry (3) and longer bantime (1 hour)
sudo bash -c 'cat <<EOF > /etc/fail2ban/jail.local
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF'

sudo systemctl restart fail2ban

# 3. SSH Specialized Configuration
sudo bash -c 'cat <<EOF > /etc/ssh/sshd_config.d/bastion-security.conf
PermitRootLogin no
PasswordAuthentication no
ClientAliveInterval 300
ClientAliveCountMax 0
MaxAuthTries 3
LoginGraceTime 60
EOF'

sudo systemctl restart ssh

# 4. Configure Automatic Security Updates
sudo dpkg-reconfigure -plow unattended-upgrades

# 5. Custom Security Banner
sudo bash -c 'cat <<EOF > /etc/issue
***************************************************************************
*                           ⚠️ AUTHORIZED ACCESS ONLY ⚠️                      *
*                                                                         *
* This system is restricted to authorized users only. All activities are  *
* logged and monitored. If you are not authorized, DISCONNECT NOW.        *
***************************************************************************
EOF'
sudo ln -sf /etc/issue /etc/motd

# 6. UFW - Only allow SSH (Port 22)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw --force enable

echo "------------------------------------------------"
echo "✅ Aggressive Bastion Hardening Complete!"
echo "------------------------------------------------"
