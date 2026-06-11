# PIMS Service - Server Migration Guide (Hostinger KVM 2)

This guide provides instructions and scripts to migrate and deploy the Psychological Intervention Platform (PIMS) from scratch on a **Hostinger KVM 2 VPS**.

---

## Hostinger KVM 2 Specifications & Environment
* **OS**: Ubuntu 22.04 LTS or 24.04 LTS (minimal, clean installation).
* **Default User**: `root`
* **Port bindings**: We recommend binding the Docker stack directly to port `80` (HTTP) on the host VM, or using a local Nginx reverse proxy with Certbot for SSL.
* **Target Timezone**: `Asia/Karachi` (PKT) for longitudinal daily reflection schedules.

---

## Folder Structure

* **`setup_server.sh`**: Runs on your new Hostinger KVM 2 VPS to install Docker, configure timezones (Asia/Karachi), install system utilities, and set up the UFW firewall.
* **`env.template`**: Template for the production environment configuration `.env` file.
* **`deploy.py`**: A python script executed on your local machine to automatically package, upload, configure, and restart the PIMS service on your Hostinger VPS.
* **`backup_restore.sh`**: A shell script to run on the server for database backup (pg_dump) and restoration.

---

## Step-by-Step Migration & Deployment Checklist

### Step 1: Point DNS to Hostinger VPS
1. Get the dedicated IPv4 address of your new Hostinger KVM 2 VPS from the hPanel dashboard.
2. Go to your DNS provider (e.g., Cloudflare, GoDaddy, Hostinger DNS) and update the `A` records for `psycheversity.com` (and `www.psycheversity.com`) to point to the new Hostinger IP address.

### Step 2: Initialize the Hostinger VPS
1. Upload the `setup_server.sh` script to your new Hostinger server using `scp` (logged in as `root`):
   ```bash
   scp setup_server.sh root@<your-hostinger-ip>:/tmp/setup_server.sh
   ```
2. SSH into your Hostinger server and execute the script:
   ```bash
   ssh root@<your-hostinger-ip>
   chmod +x /tmp/setup_server.sh
   /tmp/setup_server.sh
   ```
3. The script will configure the timezone to `Asia/Karachi`, install Docker/Docker Compose, and enable UFW allowing ports `22`, `80`, `443`, and `4756`.

### Step 3: Configure Environment Variables
1. Make a copy of `env.template` locally and name it `env.production`.
2. Edit `env.production` with your secure production values:
   * **`SECRET_KEY`**: Generate a secure string: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   * **`DATABASE_URL`**: Update username and password.
   * **`CORS_ALLOWED_ORIGINS` & `CSRF_TRUSTED_ORIGINS`**: Point to `https://psycheversity.com` and `http://psycheversity.com`.
   * **Email Settings**: Fill in your Brevo SMTP username (login email) and password (SMTP key).
   * **`NGINX_PORT`**: 
     * **Option A (Direct Port 80)**: Set `NGINX_PORT=80` if you want the Docker container to serve traffic directly on standard HTTP.
     * **Option B (Proxy Port 4756)**: Set `NGINX_PORT=4756` if you are proxying traffic via a host-level Nginx or Cloudflare Tunnel.

### Step 4: Run the Deployment Automation Script
1. Open `deploy.py` on your local machine.
2. Update the connection variables at the top of the script:
   * `VM_HOST`: Set to your new Hostinger VPS IP.
   * `VM_USER`: Set to `"root"`.
   * `VM_PASSWORD`: Set to your Hostinger VPS root password.
   * `REMOTE_DIR`: Set to `/root/psych_experiment_platform`.
3. Execute the script from your local terminal:
   ```bash
   python deploy.py
   ```
4. This script will automatically package the local code, upload it, deploy the environment configuration, build the Docker containers, run Django migrations, and seed all scale/activity data.

### Step 5: Database Migration (Importing Data)
To migrate database records from the old server to Hostinger:
1. **On the old server**: Run the backup script to dump the PostgreSQL database:
   ```bash
   chmod +x backup_restore.sh
   ./backup_restore.sh backup
   ```
2. **Download the backup**: Copy the backup file (stored in `./backups/pims_backup_*.sql.gz`) from the old server to your local machine.
3. **Upload to Hostinger**: Upload the file to your new Hostinger directory:
   ```bash
   scp backups/pims_backup_*.sql.gz root@<your-hostinger-ip>:/root/psych_experiment_platform/
   ```
4. **On the Hostinger VPS**: Run the restore command:
   ```bash
   cd /root/psych_experiment_platform
   chmod +x backup_restore.sh
   ./backup_restore.sh restore pims_backup_*.sql.gz
   ```

### Step 6: SSL Configuration (Optional)
If you are routing traffic directly (without Cloudflare proxy SSL) and want to terminate SSL directly on the Hostinger VPS:
1. Install certbot on the host VPS:
   ```bash
   sudo apt-get install -y certbot
   ```
2. Temporarily stop the Docker Nginx container if it binds to port 80, or use the webroot plugin to generate Let's Encrypt certificates for `psycheversity.com`.
3. Set up the certificates directory path mapping in `docker-compose.yml` to feed certificates into the Docker Nginx service.
