# Application Setup

Two development workflows are supported:

1. Docker Compose, recommended for reproducibility.
2. Native Python and PostgreSQL, retained for contributors who prefer local
   services.

Use one workflow at a time. They can use different PostgreSQL instances.

## Docker Compose setup

### Requirements

- Git
- Docker Desktop, or Docker Engine with Compose

Verify Docker:

```bash
docker --version
docker compose version
docker info
```

### Clone the repository

```bash
git clone <repository-url> auth
cd auth
git switch dev
```

### Configure the environment

```bash
cp .env.example .env
```

Set strong local values:

```dotenv
SECRET_KEY=replace-with-a-strong-random-secret
JWT_SECRET_KEY=replace-with-a-different-strong-random-secret
JWT_ACCESS_TOKEN_MINUTES=15
JWT_REFRESH_TOKEN_DAYS=30

APP_PORT=5001
POSTGRES_DB=auth
POSTGRES_USER=auth
POSTGRES_PASSWORD=replace-with-a-local-database-password
```

`DATABASE_URL` using `localhost` remains in `.env` for native development.
Compose overrides it inside the web and migration containers with a URL whose
host is `db`, the PostgreSQL service name.

Never commit `.env`.

### Build and start

```bash
docker compose up -d --build
```

Startup order:

```text
PostgreSQL starts and becomes healthy
    → migrate runs flask db upgrade
    → migrate exits with code 0
    → web starts Gunicorn
```

Inspect all services:

```bash
docker compose ps --all
```

Expected:

```text
db       Up (healthy)
migrate  Exited (0)
web      Up
```

`Exited (0)` means the one-off migration completed successfully.

Inspect logs:

```bash
docker compose logs
docker compose logs web
docker compose logs db
docker compose logs migrate
```

### Seed RBAC and the first Admin

```bash
docker compose exec web flask seed-db
```

The command securely prompts for the Admin details. It creates or synchronizes:

- Employee, Accountant, Manager, and Admin roles
- Seeded permissions and exact role-permission mappings
- The bootstrap Admin

Run this before accepting registrations because normal registration requires
the Employee role.

### Use the application

Open `http://localhost:5001`.

| Page | Purpose |
|---|---|
| `/login` | Sign in with username or email |
| `/register` | Create an Employee account |
| `/dashboard` | Resolve the dashboard for the current role |
| `/admin` | Admin dashboard |
| `/manager` | Manager dashboard |
| `/accountant` | Accountant dashboard |
| `/employee` | Employee dashboard |

Verify liveness:

```bash
curl http://localhost:5001/health/live
```

### Stop or reset Compose

Stop containers and preserve PostgreSQL data:

```bash
docker compose down
```

Restart later:

```bash
docker compose up -d
```

Delete containers, network, and database volume:

```bash
docker compose down --volumes
```

The final command permanently deletes the Compose database.

## Native development alternative

### Requirements

- Git
- Python with `venv`
- PostgreSQL installed and running locally

### Install

```bash
git clone <repository-url> auth
cd auth
git switch dev
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

On Windows:

```text
.venv\Scripts\activate
```

Create a local PostgreSQL database and configure:

```dotenv
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/auth
```

Apply migrations and seed:

```bash
flask db upgrade
flask seed-db
```

Run Flask:

```bash
flask run
```

Open `http://localhost:5000`.

### Native database reset

> Never run this against a production or shared database.

```bash
flask db downgrade base && flask db upgrade && flask seed-db
```

Normal updates require only:

```bash
flask db upgrade
```
