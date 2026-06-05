# PROJECT: REMEDITRACk

**A Cloud-Based Secure Vulnerability Management System**  
**AWS Region:** ap-south-1 (Mumbai)  
**Infrastructure as Code:** Terraform  
**CI/CD:** GitHub Actions  

---

## 1. Architecture Diagram & Technical Explanation

The infrastructure for RemediTrack is engineered for high availability, security isolation, and scalability. The architecture follows the AWS Well-Architected Framework, specifically the Security and Reliability pillars.

### Networking & VPC Design
A custom Virtual Private Cloud (VPC) was created with a 10.0.0.0/16 CIDR block. To maximize security, the network was segmented into public and private tiers across multiple Availability Zones (ap-south-1a and ap-south-1b):

*   **Public Subnets:** Host the Application Load Balancer (ALB) and the Bastion Host. These are the only resources accessible from the internet.
*   **Private Subnets:** Host the Application Server (EC2) and the Database (RDS). These instances have no public IP addresses and are protected from direct external attacks.
*   **NAT Gateway:** Provisioned in the public subnet to allow private instances to download security patches and updates without exposing them to incoming internet traffic.

### Managed Services
Instead of self-hosting a database, the project utilizes Amazon RDS for PostgreSQL. This provides automated backups, patches, and high availability. Static and media assets are stored in Amazon S3, offloading the storage burden from the application server and increasing performance.

---

## 2. Security Documentation

Security was not an afterthought but was integrated into every layer of the implementation.

### Web Application Security
*   **Argon2 Hashing:** Unlike standard MD5 or SHA1, Argon2 is specifically designed to be resistant to GPU-based cracking, making user passwords extremely difficult to compromise.
*   **Injection Protection:** By utilizing the Django ORM, every database query is automatically parameterized, effectively neutralizing the risk of SQL Injection (SQLi).
*   **Content Security Policy (CSP):** We implemented a strict CSP header that restricts where scripts, styles, and fonts can be loaded from. This prevents Cross-Site Scripting (XSS) and data exfiltration.

### Server Hardening & Perimeter Defense
A multi-layered defense strategy was applied to the Linux servers (Ubuntu 22.04 LTS):

*   **SSH Gateway (Bastion):** A specialized, hardened Bastion host acts as the only entry point for administrators. It features a 5-minute idle timeout and an aggressive Fail2Ban policy that bans IPs after only 3 failed attempts.
*   **Least Privilege Security Groups:** The Application server only accepts traffic on port 80 from the Load Balancer and port 22 from the Bastion. The Database only accepts traffic from the Application server.
*   **Host Firewall (UFW):** Even within the private network, each server runs a local firewall to ensure that only expected ports are open.

---

## 3. Detailed Step-by-Step Deployment Guide

### Phase 1: Infrastructure as Code (Local Machine)
1.  Navigate to the `infra/` directory to build the cloud environment. Initialize Terraform to download AWS providers.
2.  Apply the configuration to build 33 AWS resources, including a custom VPC, RDS database, S3 buckets, and EC2 instances, providing the secure RDS password and Bastion Key name.
3.  Record the outputs (`alb_dns_name`, `bastion_public_ip`, `rds_endpoint`) for the subsequent phases.

### Phase 2: Server Hardening (On the Servers)
1.  **Bastion Host Hardening:** Securely transfer the hardening script via `scp` and execute it to implement aggressive Fail2Ban policies and SSH idle timeouts.
2.  **Application Server Hardening:** Transfer the script through the Bastion host using SSH Agent Forwarding and execute it to enable UFW, disable direct public ingress, and configure unattended-upgrades.

### Phase 3: Application & Reverse Proxy Setup
1.  **Configure Nginx:** Run the automated `setup_nginx.sh` script on the App Server to establish the reverse proxy, handle SSL headers, and link it to the production `.env` file.
2.  **Install Docker:** Update APT packages and install `docker.io` and the `docker-compose-plugin`.
3.  **Launch & Initialize:** Execute `docker compose up -d --build` to launch the Gunicorn container. Follow this immediately with `migrate` to set up the database schema, `collectstatic --noinput` to push CSS/JS to the S3 bucket with proper CORS policies, and `init_data.py` to seed default users and RBAC groups.

### Phase 4: Data Operations (Backups & Logs)
1.  **Configure Backups:** Execute `configure_backups.sh` to automate the daily RDS dump to the strictly private S3 backup bucket via a cron job.
2.  **Log Rotation:** Execute `setup_logrotation.sh` to prevent disk space exhaustion by automating log cleanup and enforcing global Docker log limits.

### Phase 5: Monitoring (CloudWatch)
1.  Execute `setup_cloudwatch.sh` on the App Server to install and configure the AWS CloudWatch agent, ensuring system metrics and logs are streamed in real-time.

### Phase 6: CI/CD Pipeline (GitHub Actions)
The project utilizes GitHub Actions for full CI/CD automation. The pipeline consists of two primary jobs:

*   **Job 1: Continuous Integration (Test):** Every push to the main branch triggers a suite of Django unit tests running on a clean Ubuntu-latest runner to ensure code quality and prevent regressions.
*   **Job 2: Continuous Deployment (Deploy):** Upon successful testing, the runner uses SSH Agent Forwarding to securely 'jump' through the Bastion host and reach the private application server. It synchronizes the code, recreates the `.env` file from secrets, and restarts the Docker containers without manual intervention.

### Phase 7: Environment Configuration (.env)
To ensure the application works perfectly in production, the `src/.env` file (or the `ENV_FILE` GitHub Secret) must contain the following variables:

```env
DEBUG=False
SECRET_KEY=your secret key
ALLOWED_HOSTS=*
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your db name
DB_USER=postgres
DB_PASSWORD=your db password
DB_HOST=your aws db host
DB_PORT=5432
AWS_STORAGE_BUCKET_NAME=your assets bucket name
AWS_S3_REGION_NAME=ap-south-1
SECURE_SSL_REDIRECT=False # ALB handles SSL termination (if any), app sees HTTP
AWS_BACKUP_BUCKET_NAME=remeditrack-backups-5a5bcac4
```

---

## 4. Monitoring Setup & Proactive Alerting

### Real-Time Logging
We configured the AWS CloudWatch Agent on the application server to stream Nginx access logs, Linux authentication logs, and application error logs directly to the AWS CloudWatch Console. This allows for centralized log analysis and long-term auditing without consuming server disk space.


### Alarms & Uptime Monitoring
To ensure high availability, we implemented three types of automated alerts:

*   **Uptime Probe:** A Route 53 global health check probes the application every 30 seconds from global locations. If the site is unreachable, an SNS email alert is triggered.
*   **Performance Alarms:** CloudWatch monitors CPU and Memory utilization, alerting administrators if the server is under excessive load.
*   **Security Alarms:** A custom Metric Filter scans system logs for SSH authentication failures, alerting the team if a brute-force attack is detected.

### Backup Strategy
Data integrity is maintained through automated daily backups. A custom Bash script performs a PostgreSQL dump, which is then encrypted and uploaded to a strictly private S3 bucket. Old backups are automatically rotated to optimize storage costs.

---

## 5. Application Overview

RemediTrack is a Vulnerability Management System (VMS) designed for security operations teams. In a modern IT landscape, tracking and remediating security weaknesses is a critical compliance requirement. This application provides the necessary structure to ensure no vulnerability is overlooked.

### Core Functionality
The application facilitates a structured workflow for identifying and fixing security issues:

*   **Analysts:** Responsible for reporting new vulnerabilities and uploading proof-of-concept screenshots.
*   **Team Leaders:** Manage teams of developers and assign vulnerabilities based on severity and workload.
*   **Developers:** Track their assigned tasks, implement fixes, and mark vulnerabilities as remediated.
*   **Admins:** Full oversight of system users, teams, and audit logs.


---

## Conclusion
The RemediTrack project successfully demonstrates a full DevSecOps lifecycle on AWS, focusing on security, automation, and reliability.
