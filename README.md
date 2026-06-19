# Psycheversity
A monolith, clinical level longitudinal psychology study platform designed to run multi week experiments. Built to handle complex, phase based participant tracking, real time safety interventions for high risk responses, and a full administrative data reporting suite.

### Backend Core
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

### Real Time & Async Architecture
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![WebSockets](https://img.shields.io/badge/WebSockets-Channels-orange?style=for-the-badge&logo=scrimba&logoColor=white)](https://channels.readthedocs.io/)
[![ASGI Daphne](https://img.shields.io/badge/ASGI-Daphne-blue?style=for-the-badge)](https://github.com/django/daphne)

### Frontend Engine
[![React 19](https://img.shields.io/badge/React-19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite 8](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![React Query](https://img.shields.io/badge/React_Query-v5-FF4154?style=for-the-badge&logo=react-query&logoColor=white)](https://tanstack.com/query/latest)

### DevOps & Infrastructure
[![Docker Compose](https://img.shields.io/badge/Docker_Compose-7_Services-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white)](https://nginx.org/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)

## Core Features & Technical Highlights

- **Automated Participant Flow**: Registration and onboarding flow with JWT-based authentication (SimpleJWT), digital consent management, and automated baseline/post-test questionnaire administration.
- **Dynamic Group Management**: Custom assignment algorithm (`groups/services.py`) that handles intelligent, balanced participant distribution into experimental control and treatment groups once the baseline (T0 SIGNUP) assessment is completed.
- **Longitudinal Daily Activities**: Timeline logic engine that serves phase-specific activities dynamically based on `experiment_day`. Features strict midnight-reset validation (standardized on Asia/Karachi time) and Redis-backed caching for state management.
- **Multilingual UI (i18n)**: Fully integrated localization (English and Urdu) via `react-i18next` with logic for Right-to-Left (RTL) styling and logical CSS properties.
- **Asynchronous Task Processing**: Celery-backed architecture for non-blocking operations, including CSV data exports (baseline/post-test analytics) and batch notifications.
- **Support Ticketing System**: Two-way communication channel with real-time polling logic for unread notification badges.

## Project Structure

### Backend (`/backend`)
Django application built with modular apps:
- `users/`: Custom User model, JWT authentication, and participant profile management.
- `groups/`: Group management, capacity configuration, and the dynamic assignment algorithm.
- `phases/`: Definition of experiment phases and their sequence logic.
- `activities/`: Core timeline engine for daily prompts, submission handling, and caching.
- `questionnaires/`: JSON-schema backed dynamic forms for baseline and post-test assessments.
- `admin_tools/`: Reporting views, CSV export tasks, and dashboard analytics.
- `support/`: Ticketing system models and API endpoints.

### Frontend (`/frontend`)
React application organized by feature:
- `src/components/`: Reusable UI elements, Navigation, and Modals.
- `src/pages/`: Route-level components for authentication, dashboards, and admin views.
- `src/services/`: Axios interceptors and API interaction layers.
- `src/locales/`: i18n translation resources for English and Urdu.

## Environment Variables & API Keys

Before running the application, you must configure a `.env` file at the root of the repository. The required keys include:

- **Django Settings**: `SECRET_KEY`, `DEBUG` (set to `False` in production), `ALLOWED_HOSTS`.
- **Database (PostgreSQL)**: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
- **Third-Party Integrations**:
  - **Mailjet**: `MAILJET_API_KEY`, `MAILJET_SECRET_KEY`, `MAILJET_SENDER_EMAIL` (Required for verification OTP emails and notifications).
  - **Twilio**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` (Required for WhatsApp notifications).
- **Frontend Variables**: `VITE_API_URL` pointing to the backend API endpoint.

## Local Development Setup

The platform is fully containerized. A `docker-compose.yml` file is provided to orchestrate the backend, frontend, PostgreSQL, and Redis containers.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pims-service/pims-service.git
   cd pims-service
   ```

2. **Configure the Environment**:
   Copy the example environment configuration and populate the required keys.
   ```bash
   cp .env.example .env
   ```

3. **Start the Development Stack**:
   This will build the images, apply Django migrations, and start the development servers.
   ```bash
   docker compose up --build
   ```

4. **Access the Services**:
   - **Frontend Application**: `http://localhost:5173`
   - **Backend API**: `http://localhost:8000/api`
   - **Django Admin Console**: `http://localhost:8000/admin`

## Production Deployment

To deploy this application on a production VPS (e.g., Hostinger KVM2):

1. **Server Provisioning**: Ensure Docker and Docker Compose are installed on your VPS (Ubuntu 22.04+ recommended).
2. **Clone and Configure**: Clone the repository and set up your `.env` file with **production credentials**, ensuring `DEBUG=False`.
3. **SSL / HTTPS (Certbot)**: It is highly recommended to secure the Nginx container using Let's Encrypt. Configure your Nginx config (`nginx/conf.d/default.conf`) to handle port 443.
4. **Deploy the Stack**:
   Use the `-d` flag to run the containers in the background as a daemon.
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```
5. **Database Migrations & Setup**:
   Run database migrations and create a superuser for the Django admin panel.
   ```bash
   docker compose exec backend python manage.py migrate
   docker compose exec backend python manage.py createsuperuser
   ```

## Architecture & Optimization

The application architecture is optimized for high concurrency environments:
- **Database Indexing**: Strategic indexing on heavily queried foreign keys (`user_id`, `activity_id`) and temporal fields to optimize PostgreSQL lookups.
- **Query Optimization**: Extensive use of Django's `select_related` and `prefetch_related` within ViewSets to prevent N+1 query problems, particularly in analytic views.
- **State Caching**: Redis is utilized heavily by the `activities` app to cache the current `experiment_day` and submission state per user, drastically reducing database load during daily peak usage.
- **Asynchronous Workers**: Resource-intensive tasks, such as generating large CSV datasets, are offloaded to Celery to prevent blocking the WSGI workers.

## Comprehensive System Documentation

Additional detailed documentation regarding system design, architectures, and operations is available inside the `/docs` folder:
- **[System Architecture](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/docs/architecture.md)**: Network port mappings and sequence flows.
- **[Database & Cache Schema](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/docs/database_schema.md)**: PostgreSQL ERD and Redis keys definitions.
- **[Participant Timeline & Flow](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/docs/participant_flow.md)**: Experiment Day calculations, state machine, and suicide risk protocols.
- **[API Reference](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/docs/api_reference.md)**: REST endpoints request payloads and response definitions.
- **[Deployment & Operations](file:///c:/Users/elmir/Desktop/experiment/psych_experiment_platform/docs/deployment_and_ops.md)**: Production guide, database backups, and Celery beat crontab lists.
