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

2. Run the setup script (creates .env, pulls images, starts services):

```bash
./scripts/setup.sh
```
The script checks for Python 3.12+, Docker, and Docker Compose v2. It creates a virtual environment, installs dependencies, generates a random JWT secret, and starts MySQL and the FastAPI app.

3. Access the application:


| Service | URL | Description |
|------------|---------|-----------|
| Swagger UI (API docs)   | http://localhost:8000/docs | Explore and test the versioned API |
| Dashboard | http://localhost:8000 | Login with a registered user, then view reports |
| MySQL      | localhost:3306 | Database (username/password from .env) |


4. Log in with a user you register via Swagger UI (POST /api/v1/auth/register). After logging in on the web interface, you can generate server reports and see them appear in the dashboard chart and table.

## What's included
| Component | Purpose | Host port |
|------------|---------|-----------|
| FastAPI app   | Backend API (JWT auth, metrics collection) | 8000 |
| MySQL 8.0 | Persistent database for users and reports | 3306 |
| Frontend      | Static HTML/CSS/JS dashboard (Bootstrap, Chart.js) | same as app (8000) |

All services are defined in compose.yaml. The app container exposes the API and serves the static frontend. MySQL has a healthcheck and a persistent volume.

## Endpoints (versioned, /api/v1)

| Method   | Endpoint                       | Description                                                                 |
|----------|--------------------------------|-----------------------------------------------------------------------------|
| POST     | `/api/v1/auth/register`        | Register a new user (email, password, full_name)                           |
| POST     | `/api/v1/auth/login`           | Login with email/password -> returns JWT                                   |
| GET      | `/api/v1/auth/me`              | Get current user info (Bearer token required)                              |
| POST     | `/api/v1/reports/`             | Generate a new server report (CPU, memory, disk, network)                  |
| GET      | `/api/v1/reports/`             | List all reports for the authenticated user                                |
| GET      | `/health/live`                 | Liveness probe for Docker                                                  |
| GET      | `/health/ready`                | Readiness probe for Docker                                                 |

All endpoints (except health) are documented in Swagger UI with examples and response schemas. The OpenAPI spec is available at /openapi.json.

## Frontend integration

The static frontend (login + dashboard) communicates with the versioned API. To build your own frontend:

Base URL: http://localhost:8000/api/v1

Authentication: store the access_token from `/login` in localStorage or a secure cookie. Include it in every request as Authorization: Bearer `<token>`.

Example registration (JavaScript):

```bash
fetch('/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'luqmaan@example.com', password: '...', full_name: 'Tech Journeys })
});
```
The dashboard source code (`frontend/js/dashboard.js`) is a complete reference.

## Health checks
The FastAPI container defines a healthcheck that polls `/health/live`. MySQL has a `mysqladmin ping` healthcheck. Docker Compose respects these – the stack starts only when both services are healthy.

## Managing the JWT secret
The JWT secret is stored in `.env` (generated automatically by `setup.sh`). To rotate it:

1. Stop the app: `docker compose down`

2. Edit `.env` and replace `JWT_SECRET` with a new random 32‑byte hex string.

3. Start again: `docker compose up -d`

Existing tokens will become invalid; users must log in again.

## Environment variables
Copy `.env.example` to `.env` (this is done by `setup.sh`). Key variables:
| Variable                                          | Description                                                                 |
|---------------------------------------------------|-----------------------------------------------------------------------------|
| `ENVIRONMENT`                                     | `development` (enable docs) or `production`                                |
| `JWT_SECRET`                                      | 32‑byte hex key (required)                                                 |
| `DATABASE_URL`                                    | Async MySQL connection string                                              |
| `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | MySQL credentials                                 |
| `LOG_LEVEL`                                       | `INFO`, `DEBUG`, etc.                                                      |
| `CORS_ORIGINS`                                    | Comma‑separated allowed origins (default: `http://localhost:8000,http://localhost:3000`) |

## Stopping the stack

```bash
docker compose down
```
Add `-v` to also remove data volumes (resets the database).

## Uninstalling the stack completely
To remove all Docker containers, networks, volumes, and the generated `.env` file, run:

```bash
./scripts/uninstall.sh
```

## Troubleshooting
Containers restarting / healthcheck failing: Check logs with `docker compose logs app` or `docker compose logs mysql`.

Swagger UI shows only health endpoints: Make sure `ENVIRONMENT=development` in `.env`.

Login redirects back to login page: Open browser console – likely the token is not stored. Verify `frontend/js/login.js` uses the correct endpoint (`/api/v1/auth/login`) and that the browser allows localStorage.
 
Reports endpoint returns 500 / table missing: Run `docker compose exec app alembic upgrade head` to apply database migrations.

Port conflicts: Change the host ports in compose.yaml (e.g., "8000:8000" -> "8001:8000").

Can't connect to MySQL: Ensure the MySQL container is healthy (`docker compose ps`). The app uses the service name `mysql` as hostname, which works inside the Docker network.

## License
MIT. See `LICENSE`.
