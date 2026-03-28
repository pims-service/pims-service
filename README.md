# Psychological Experiment Platform

A full-stack platform designed for phased psychological experiments with 2,000+ participants. Optimized for Hostinger KVM2 VPS.

## Tech Stack
- **Backend**: Django, Django REST Framework, PostgreSQL
- **Frontend**: React (Vite), TypeScript, Tailwind CSS, Chart.js
- **Auth**: JWT (SimpleJWT)
- **Notifications**: SendGrid (Email), Twilio (WhatsApp) - Placeholders ready.

## Directory Structure
- `backend/`: Django core, apps (users, groups, phases, activities, notifications, admin_tools).
- `frontend/`: React components, pages, hooks, services.
- `docs/`: SPSS export templates and project documentation.

## Setup Instructions

### Backend Setup
1. Navigate to `backend/`.
2. Create/Activate virtual environment: `python -m venv venv && source venv/bin/activate`.
3. Install dependencies: `pip install -r requirements.txt` (Note: Generate this if needed).
4. Configure `.env` in the root folder (see template).
5. Run migrations: `python manage.py migrate`.
6. Start server: `python manage.py runserver`.

### Frontend Setup
1. Navigate to `frontend/`.
2. Install dependencies: `npm install`.
3. Start development server: `npm run dev`.

## Concurrent User Optimization (1,000+ Users)

To handle 1,000 concurrent users on a Hostinger KVM2 (4GB RAM/2 vCPU):

### 1. Database Layer
- **Indexing**: Ensure all foreign keys and frequently filtered fields (e.g., `user_id`, `activity_id`, `start_date`) are indexed in PostgreSQL.
- **Connection Pooling**: Use **PgBouncer** to manage a large number of database connections efficiently.
- **Optimized Queries**: Use `select_related` and `prefetch_related` in Django to reduce the number of queries.

### 2. Caching
- **Redis**: Implement Redis for caching frequent API responses (e.g., dashboard activity lists, participant stats).
- **Session Backend**: Use Redis as the Django session engine for faster read/writes.

### 3. Application Server
- **Workers**: Configure Gunicorn with `(2 * CPU + 1)` workers. For KVM2, try 5 workers.
- **Asynchronous Tasks**: Use **Celery** with Redis/RabbitMQ for background tasks like sending 2,000+ notifications to avoid blocking the request cycle.

### 4. Frontend & Static Files
- **CDN**: Use a CDN (e.g., Cloudflare) for serving static assets.
- **Whitenoise**: Configure Whitenoise with compression and caching headers for efficient static file serving from Django.
