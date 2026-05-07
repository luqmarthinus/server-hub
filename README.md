# Server Hub

A full‑stack server monitoring hub – FastAPI backend + interactive dashboard. Collects real‑time system metrics (CPU, memory, disk, network) and provides user authentication with JWT. The backend uses MySQL (Docker), Alembic migrations, and modern Python async. The frontend is a responsive dashboard with Chart.js and Bootstrap 5.

## Badges

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Docker](https://img.shields.io/badge/docker-%3E%3D26-2496ED?logo=docker&logoColor=white)
![Compose](https://img.shields.io/badge/compose-v2-8c8c8c?logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-grey?logo=fastapi)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)

## Quick start

1. Clone the repository:

```bash
git clone https://github.com/luqmarthinus/server-hub.git
cd server-hub
```

2. Create the environment file and generate a JWT secret:

```bash
cp .env.example .env
# Generate a secure JWT secret (32 bytes hex)
printf "\nJWT_SECRET=%s\n" "$(openssl rand -hex 32)" >> .env
```
3. Start the stack:

  ```bash
docker compose up -d
```

4. Access the application:


| Service                  | URL                          | Description                                         |
|---------------------------|-------------------------------|-----------------------------------------------------|
| Swagger UI (API docs)     | http://localhost:8000/docs    | Explore and test the versioned API                  |
| Registration page         | http://localhost:8000/register | Create a new user account                           |
| Login page                | http://localhost:8000/login   | Sign in with your credentials                       |
| Dashboard                 | http://localhost:8000         | View and generate server reports (after login)      |
| Admin panel               | http://localhost:8000/admin   | Manage users (super admin only)                     |
| MySQL                     | localhost:3306                | Database (credentials from `.env`)                    |


A default super admin account is created on first startup:

Email: `server_admin@example.com`

Password: `mzansi2026`

Change the password after first login via the Profile page.

---

## What's included
| Component | Purpose | Host port |
|------------|---------|-----------|
| FastAPI app   | Backend API (JWT auth, metrics collection, Slack alerts, background scheduler) | 8000 |
| MySQL 8.0 | Persistent database for users and reports | 3306 |
| Frontend      | Static HTML/CSS/JS dashboard (Bootstrap, Chart.js) | served by app on same port |

All services are defined in `compose.yaml`. The app container exposes the API and serves the static frontend. MySQL has a healthcheck and a persistent volume. The container runs `alembic upgrade head` on startup, ensuring the database schema is always up to date.

---

## Endpoints (versioned, /api/v1)

## Authentication

| Method | Endpoint | Description |
|--------|-----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user (email, password, full_name) |
| POST | `/api/v1/auth/login` | Login with email/password -> returns JWT |
| GET | `/api/v1/auth/me` | Get current user info (Bearer token required) |
| PUT | `/api/v1/auth/change-password` | Change own password (current password required) |
| DELETE | `/api/v1/auth/delete-account` | Delete own account and all associated reports |

---

## Reports

| Method | Endpoint | Description |
|--------|-----------|-------------|
| POST | `/api/v1/reports/` | Generate a new server report (CPU, memory, disk, network) |
| GET | `/api/v1/reports/` | List all reports for the authenticated user (supports days filter) |
| DELETE | `/api/v1/reports/{report_id}` | Delete a specific report (owner only) |
| GET | `/api/v1/reports/export` | Download reports as CSV (optional days parameter) |

---

## System

| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/api/v1/system/info` | System information (hostname, OS, CPU, memory, disk) – authenticated |
| POST | `/api/v1/system/stress/cpu` | Run 5-second CPU stress test (super admin only) |
| POST | `/api/v1/system/stress/memory` | Allocate 200MB memory then free (super admin only) |
| POST | `/api/v1/system/stress/disk` | Write 200MB temp file and delete (super admin only) |

---

## Admin (super admin only)

| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/api/v1/admin/users` | List all users with report counts |
| POST | `/api/v1/admin/users` | Create a new user (email, full_name, password) |
| DELETE | `/api/v1/admin/users/{user_id}` | Delete a user (cannot delete yourself or the only super admin) |
| PUT | `/api/v1/admin/users/{user_id}/role` | Toggle is_superuser flag |

---

## Health

| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/health/live` | Liveness probe for Docker |
| GET | `/health/ready` | Readiness probe for Docker |

All endpoints are documented in Swagger UI with examples and response schemas. The OpenAPI spec is available at `/openapi.json`.

---

## Frontend integration

The static frontend (login, registration, dashboard, admin panel, profile) communicates with the versioned API. To build your own frontend:

Base URL: http://localhost:8000/api/v1

Authentication: Store the access_token from `/login` in localStorage. Include it in every request as `Authorization: Bearer <token>`.

Example registration (JavaScript):

```bash
fetch('/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'luqmaan@example.com', password: '...', full_name: 'Tech Journeys })
});
```
The dashboard source code (`frontend/js/dashboard.js`) is a complete reference.

---

## Slack alerts

When a report is generated (manually, via stress test, or by the background scheduler), the application checks CPU, memory, and disk usage against thresholds defined in .env. If any threshold is exceeded, a message is sent to the configured Slack webhook.

`SLACK_WEBHOOK_URL`: your Slack incoming webhook URL (create one in your Slack workspace).

`ALERT_CPU_THRESHOLD`, `ALERT_MEMORY_THRESHOLD`, `ALERT_DISK_THRESHOLD`: values in percent (default 80, 90, 90).

The background scheduler runs every minute and automatically generates a report (using the first super admin user) to continuously monitor system health.

---

## Backup and restore
Use the provided `backup.sh` script to safely back up and restore the MySQL database.

## Prerequisites
Docker Compose stack must be running (`docker compose up -d`)

`.env` file with MYSQL_ROOT_PASSWORD set

## Backup Commands

| Command | Description |
|---------|-------------|
| `./backup.sh backup` | Create a timestamped SQL backup in `./backups/` |
| `./backup.sh list` | List all available backup files |
| `./backup.sh restore <filename.sql>` | Restore the database from a backup file (confirmation required) |

## Example

```bash
# Create a backup
./backup.sh backup

# List backups
./backup.sh list

# Restore a specific backup
./backup.sh restore backups/backup_20250507_143022.sql
```

---

## Notes
The script reads `MYSQL_ROOT_PASSWORD` and `MYSQL_DATABASE` from your `.env` file.

Restore drops and recreates the database – all current data is lost. You are prompted to confirm.

Backups include stored procedures and triggers (`--routines --triggers`).

The backup directory `./backups/` is ignored by Git (added to `.gitignore`).

---

## Environment Variables

Key variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `ENVIRONMENT` | `development` (enables Swagger UI) or `production` |
| `JWT_SECRET` | 32-byte hex key (required, generated on first setup) |
| `DATABASE_URL` | Async MySQL connection string |
| `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | MySQL credentials |
| `LOG_LEVEL` | `INFO`, `DEBUG`, etc. |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL (optional, alerts) |
| `ALERT_CPU_THRESHOLD`, `ALERT_MEMORY_THRESHOLD`, `ALERT_DISK_THRESHOLD` | Alert thresholds in percent |

---

## Health checks
The FastAPI container defines a healthcheck that polls `/health/live`. MySQL has a `mysqladmin ping` healthcheck. Docker Compose respects these as the stack starts only when both services are healthy.


## Stopping the stack

```bash
docker compose down
```
Add `-v` to remove ALL containers, networks and data volumes.

This leaves only the repository code. You can rebuild later with docker compose up -d.

---

## Troubleshooting
Containers restarting/healthcheck failing: Check logs with `docker compose logs app` or `docker compose logs mysql`.

Swagger UI shows only health endpoints: Set `ENVIRONMENT=development` in `.env` and restart.

Login redirects back to login page: Open browser console. Verify `frontend/js/login.js` uses the correct endpoint (`/api/v1/auth/login`) and that the browser allows `localStorage`.

Reports endpoint returns 500/table missing: Run `docker compose exec app alembic upgrade head` to apply database migrations. If the error persists, the entrypoint script should handle it automatically on container start.

Port conflicts: Change the host ports in `compose.yaml` (e.g., "8000:8000" → "8001:8000").

Can't connect to MySQL: Ensure the MySQL container is healthy (`docker compose ps`). The app uses the service name `mysql` as hostname, which works inside the Docker network.

Stress tests not visible or returning 403: Stress test buttons are hidden for non‑superadmin users. Log in as a super admin (`server_admin@example.com`/`mzansi2026`).

## License
MIT. See `LICENSE`.
