# RemediTrack: Secure Cloud-Based Web Application (DevSecOps)

RemediTrack is a Django-based Vulnerability Management System (VMS) deployed on a high-security AWS infrastructure. This project demonstrates a complete DevSecOps lifecycle, including Infrastructure as Code (IaC), automated CI/CD pipelines, server hardening, and proactive monitoring.

## 🏗️ Project Architecture
The architecture is designed for maximum security isolation:
- **Network:** Custom VPC with Public Subnets (ALB, Bastion) and Private Subnets (App Server, RDS).
- **Compute:** Ubuntu EC2 instances in private subnets, accessible only via a Bastion Host gateway.
- **Load Balancing:** Application Load Balancer (ALB) handles public traffic and terminates SSL.
- **Database:** Managed Amazon RDS for PostgreSQL.
- **Storage:** Amazon S3 for static assets and private, encrypted database backups.

## 🛠️ Prerequisites
Before starting, ensure you have:
1. **AWS CLI** installed and configured (`aws configure`).
2. **Terraform** installed on your local machine.
3. **An AWS Key Pair** named `Remeditrack_Bastion` in the `ap-south-1` region.
4. **GitHub Account** for CI/CD automation.

---

## 🚀 Step-by-Step Deployment Guide

### Phase 1: Infrastructure as Code (Local Machine)
Navigate to the `infra/` directory to build the cloud environment:
```bash
cd infra
terraform init
terraform apply -var="db_password=YourSecurePassword" -var="key_name=Remeditrack_Bastion"
```
**Important:** Note the outputs (`alb_dns_name`, `bastion_public_ip`, `rds_endpoint`) for the next phases.

### Phase 2: Server Hardening (On the Servers)
Security must be applied at the OS level.

1. **Harden the Bastion Host:**
   ```bash
   scp -i your-key.pem scripts/bastion_hardening.sh ubuntu@<BASTION_IP>:/home/ubuntu/
   ssh -i your-key.pem ubuntu@<BASTION_IP> "chmod +x bastion_hardening.sh && ./bastion_hardening.sh"
   ```

2. **Harden the Application Server:**
   Transfer the script through the Bastion:
   ```bash
   ssh -A -J ubuntu@<BASTION_IP> ubuntu@<SERVER_PRIVATE_IP> "curl -O https://raw.githubusercontent.com/.../app_server_hardening.sh && chmod +x app_server_hardening.sh && ./app_server_hardening.sh"
   ```

### Phase 3: Application & Reverse Proxy Setup
1. **Configure Nginx:** Run the automated script on the App Server to set up the reverse proxy and link it to your `.env` file.
   ```bash
   # On the App Server
   sudo ./scripts/setup_nginx.sh
   ```
2. **Install and Launch Docker:**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-plugin
   cd src
   docker compose up -d --build
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py collectstatic --noinput
   docker compose exec web python init_data.py
   ```

### Phase 4: Data Operations (Backups & Logs)
1. **Configure Backups:** Automate the daily RDS dump to the private S3 bucket.
   ```bash
   # On the App Server
   sudo ./scripts/configure_backups.sh
   ```
2. **Log Rotation:** Prevent disk space issues by automating log cleanup.
   ```bash
   # On the App Server
   sudo ./scripts/setup_logrotation.sh
   ```

### Phase 5: Monitoring (CloudWatch)
Install and configure the CloudWatch agent to stream logs and system metrics.
```bash
# On the App Server
sudo ./scripts/setup_cloudwatch.sh
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)
The project is configured for automated deployment via GitHub Actions. Every push to the `main` branch triggers a workflow that:
1. Runs automated unit tests.
2. Securely connects to the Bastion host via SSH.
3. Synchronizes the latest code to the App Server.
4. Restarts the Docker containers.

### Required GitHub Secrets:
Add these under **Settings > Secrets and variables > Actions**:
- `SSH_PRIVATE_KEY`: Content of your `.pem` key.
- `BASTION_IP`: Public IP of the Bastion.
- `SERVER_IP`: Private IP of the App Server.
- `ENV_FILE`: Full content of your production `.env` (Include DB and S3 credentials).

## ⚙️ Environment Configuration (.env)

To ensure the application works perfectly in production, your `src/.env` file (or the `ENV_FILE` GitHub Secret) must contain the following variables:

```env
DEBUG=False
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=*
DB_ENGINE=django.db.backends.postgresql
DB_NAME=remeditrack_db
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=your_aws_db_host
DB_PORT=5432
AWS_STORAGE_BUCKET_NAME=your_assets_bucket_name
AWS_S3_REGION_NAME=ap-south-1
SECURE_SSL_REDIRECT=False # ALB handles SSL termination (if any), app sees HTTP
AWS_BACKUP_BUCKET_NAME=your_backup_bucket_name
```



---

## 📁 Directory Structure
- `/docs`: Architecture diagram and docs
- `infra/`: Terraform files for AWS resource management.
- `scripts/`: Automation scripts for hardening, Nginx, backups, and monitoring.
- `src/`: Django application source code, Dockerfile, and configurations.
- `.github/`: CI/CD workflow definitions.



## 🔍 Verification
- **Web App:** Visit the `alb_dns_name` in your browser.
- **Monitoring:** Check AWS CloudWatch -> Log Groups -> `remeditrack/nginx/access`.
- **Backups:** Check the private S3 bucket `remeditrack-backups-xxxx`.
