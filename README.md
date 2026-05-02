# Psychological Experiment Platform

A comprehensive, full-stack platform designed to facilitate phased psychological experiments. The system is engineered to securely manage participant data, orchestrate daily longitudinal activities, and provide robust administrative oversight for large-scale studies.

## Core Features & Technical Highlights

- **Automated Participant Flow**: Registration and onboarding flow with JWT-based authentication (SimpleJWT), digital consent management, and automated baseline/post-test questionnaire administration.
- **Dynamic Group Management**: Custom assignment algorithm (`groups/services.py`) that handles intelligent, balanced participant distribution into experimental control and treatment groups based on current capacity.
- **Longitudinal Daily Activities**: Timeline logic engine that serves phase-specific activities dynamically based on `experiment_day`. Features strict midnight-reset validation and Redis-backed caching for state management.
- **Multilingual UI (i18n)**: Fully integrated localization (English and Urdu) via `react-i18next` with logic for Right-to-Left (RTL) styling and logical CSS properties.
- **Asynchronous Task Processing**: Celery-backed architecture for non-blocking operations, including CSV data exports (baseline/post-test analytics) and batch notifications.
- **Support Ticketing System**: Two-way communication channel with real-time polling logic for unread notification badges.

## Technology Stack

### Backend
- **Framework**: Django 5.x, Django REST Framework
- **Database**: PostgreSQL
- **Caching & Message Broker**: Redis
- **Task Queue**: Celery
- **Authentication**: JWT (djangorestframework-simplejwt)

### Frontend
- **Framework**: React 18 (Vite), TypeScript
- **Styling**: Tailwind CSS
- **State Management & Routing**: React Router DOM, React Hooks
- **Visualization**: Chart.js / react-chartjs-2

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server / Reverse Proxy**: Nginx
- **WSGI Server**: Gunicorn

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
  - **SendGrid**: `SENDGRID_API_KEY` (Required for transactional emails like password resets and notifications).
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
