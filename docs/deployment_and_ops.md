# Deployment & Operations Guide

This document provides administrative and operations instructions for running the Psychological Experiment Platform in development and production environments.

---

## 1. Local Development Setup

The development environment runs inside Docker Compose containers, mirroring production services.

### Prerequisites
* Docker Desktop (v20.10+)
* Docker Compose (v2.x+)
* Ports `80` and `8000` must be available on the host machine.

### Commands Quick Start
1. **Initialize configurations:**
   ```bash
   cp .env.example .env
   ```
2. **Build and start services:**
   ```bash
   docker compose up --build -d
   ```
3. **Run migrations and seeds:**
   ```bash
   # Run DB Migrations
   docker exec -it psych_backend python manage.py migrate
   # Seed roles and sample experimental groups
   docker exec -it psych_backend python manage.py seed_questionnaires
   docker exec -it psych_backend python manage.py seed_daily_tasks
   ```

---

## 2. Timezone Configuration (Asia/Karachi)

To ensure daily reflection limits roll over exactly at midnight local time, all containers must follow the Pakistani Standard Time (`Asia/Karachi`) timezone.

* **Environment Variable:** The `TZ: Asia/Karachi` variable is injected into `db`, `backend`, `celery_worker`, and `celery_beat` services via [docker-compose.yml](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/docker-compose.yml).
* **Verify System Clock:** Run the following command on the host to check the container clock:
  ```bash
  docker exec -it psych_backend date
  # Expected output should show PKT suffix:
  # Sat Jun  6 20:30:00 PKT 2026
  ```

---

## 3. Celery Beat Schedule

The `celery_beat` container enqueues periodic tasks using cron rules defined in [settings.py](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/backend/core/settings.py). Since `CELERY_ENABLE_UTC = False`, all crontab entries execute in local Pakistani Standard Time:

| Task Name | Cron Schedule (PKT) | Target Task | Description |
| :--- | :--- | :--- | :--- |
| `daily-morning-reminder` | `0 9 * * *` (9:00 AM) | `notifications.tasks.check_and_send_daily_reminders` | Sends WhatsApp/email alerts to users who haven't completed reflections. |
| `daily-evening-reminder` | `0 18 * * *` (6:00 PM) | `notifications.tasks.check_and_send_daily_reminders` | Sends high-priority evening nudges to users who still need to submit reflections. |
| `tier3-daily-evaluation` | `0 1 * * *` (1:00 AM) | `notifications.tasks.run_tier3_daily_evaluation` | Scans for users past Day 8 with low activity rates to generate clinical call tickets. |
| `assessment-graduated-reminders` | `0 2 * * *` (2:00 AM) | `notifications.tasks.run_assessment_graduated_reminders` | Triggers SMS, WhatsApp, and email alerts for overdue psychometric assessments. |
| `daily-suicide-risk-admin-cache` | `0 3 * * *` (3:00 AM) | `questionnaires.tasks.refresh_suicide_risk_admin_cache` | Clears and rebuilds the Redis cache for flagged risk cases on the dashboard. |

---

## 4. Production Operations

### 4.1 Database Backups (PostgreSQL)
Backups should be enqueued via local host crontab.
* **Generate Backup File:**
  ```bash
  docker exec -t psych_db pg_dumpall -c -U psych_user > /var/backups/psych_db_backup_$(date +%F).sql
  ```
* **Restore from Backup File:**
  ```bash
  docker exec -i psych_db psql -U psych_user -d psych_db < /var/backups/psych_db_backup_xxxx-xx-xx.sql
  ```

### 4.2 Cache Invalidation & Administration
If a participant complains about stale stats or dashboard lockups:
* **Clear all Redis caches (Force Reset):**
  ```bash
  docker exec -it psych_backend python manage.py shell -c "from django.core.cache import cache; cache.clear()"
  ```
* **View running background workers:**
  ```bash
  docker exec -it psych_celery_worker celery -A core status
  ```

### 4.3 Month-3 PDF Report Generation Dependencies
The automated Month-3 PERMA trajectory report requires HTML-to-PDF conversion (`weasyprint`) and chart plotting (`matplotlib`).
* **System Libraries (Cairo & Pango)**: WeasyPrint depends on system packages for font configuration and rendering:
  * Debian/Ubuntu dependencies (configured in `backend/Dockerfile`): `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz0b`, `libpangocairo-1.0-0`, `libffi-dev`, `libcairo2`, `libgdk-pixbuf-2.0-0`, `shared-mime-info`, `fontconfig`.
* **Urdu RTL Nastaleeq Font Configuration**:
  * The PDF requires the custom TrueType font `JameelNooriNastaleeq.ttf` for correct Nastaleeq script layout and Urdu characters rendering.
  * The font file is copied into `/usr/share/fonts/truetype/JameelNooriNastaleeq.ttf` in the backend container, and the font cache is rebuilt using `fc-cache -f -v` during the image build process.

### 4.4 Git-Tracking of Static Assets for CI/CD Builds
By default, `.gitignore` excludes `/backend/static/` subfolders or files from Git tracking. However, critical runtime assets like fonts (`JameelNooriNastaleeq.ttf`) and brand logos (`pims_logo.png`, `pims_logo-removebg.png`) must be present in the repository so the docker-build context succeeds on GitHub Actions runner.
* **Workaround**: You must force-stage ignored static files before pushing to remote VM or repository:
  ```bash
  git add -f backend/static/fonts/JameelNooriNastaleeq.ttf
  git add -f backend/static/pims_logo.png
  git add -f backend/static/pims_logo-removebg.png
  ```
* Failures to do this will trigger `COPY failed: no such file or directory` errors during the docker image build phase in the CI pipeline.

