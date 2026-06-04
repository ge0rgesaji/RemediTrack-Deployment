#!/bin/bash
set -e

echo "Starting Server Hardening..."

# 1. SSH Hardening
sudo sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 2. Install fail2ban
sudo apt update
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 3. UFW Firewall Setup
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw --force enable

echo "Hardening Complete!"
