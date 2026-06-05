#!/bin/bash
# RemediTrack Nginx Setup Script
set -e

# --- CONFIGURATION ---
ENV_FILE="/home/ubuntu/Remeditrack-Devops/src/.env"

# Fetch the first domain from ALLOWED_HOSTS in .env
if [ -f "$ENV_FILE" ]; then
    # Extract the first value before the first comma
    DOMAIN=$(grep '^ALLOWED_HOSTS=' $ENV_FILE | cut -d '=' -f2 | cut -d ',' -f1)
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

if [ -z "$DOMAIN" ]; then
    echo "Error: Could not find domain in ALLOWED_HOSTS in $ENV_FILE"
    exit 1
fi

APP_PORT="8000"
NGINX_CONF="/etc/nginx/sites-available/remeditrack"


echo "Installing Nginx and Configuring Reverse Proxy..."

# 1. Install Nginx
sudo apt update
sudo apt install -y nginx

# 2. Remove default Nginx site
if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

# 3. Create RemediTrack Configuration
echo "Creating Nginx configuration for $DOMAIN..."
sudo bash -c "cat <<EOF > $NGINX_CONF
server {
    listen 80 default_server;
    server_name $DOMAIN;

    # Maximum upload size for screenshots
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Standard timeouts
        proxy_connect_timeout 90;
        proxy_send_timeout 90;
        proxy_read_timeout 90;
    }

    # Optional: Serve local media if not using S3
    location /media/ {
        alias /home/ubuntu/Remeditrack-Devops/src/media/;
    }
}
EOF"

# 4. Enable the site and test
if [ ! -f /etc/nginx/sites-enabled/remeditrack ]; then
    sudo ln -s $NGINX_CONF /etc/nginx/sites-enabled/
fi

sudo nginx -t

# 5. Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx


echo "Nginx is now running as a Reverse Proxy!"
