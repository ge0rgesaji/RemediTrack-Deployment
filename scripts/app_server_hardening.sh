#!/bin/bash
set -e
 
echo  "Starting APP SERVER HARDENING"

# 1. Update and install necessary tools
sudo apt update
sudo apt install -y unattended-upgrades

# 2. SSH Hardening
# No root login, No passwords
sudo sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 3. Configure Automatic Security Updates
# Important for keeping the OS safe without manual work
sudo dpkg-reconfigure -plow unattended-upgrades

# 4. UFW Firewall Setup
# Note: Fail2Ban is NOT installed here per your request.
# We rely on the Bastion host to block brute-force attacks.
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw --force enable

echo  "Done APP SERVER HARDENING"
