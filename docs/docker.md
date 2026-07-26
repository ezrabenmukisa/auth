# Docker and Clean-Checkout Guide

## Container design

The project uses:

```text
Application image
├── Python 3.14
├── Runtime dependencies
├── Application source and migrations
├── Non-root appuser
└── Gunicorn

Compose stack
├── web       Long-running application container
├── migrate   One-off Alembic migration container
└── db        PostgreSQL 17 container with persistent volume
```

The web and migration services are built from the same Dockerfile. The
migration service replaces the image's default Gunicorn command with
`flask db upgrade`.

The image never contains `.env`, the virtual environment, database files, raw
passwords, JWTs, tests, or documentation.

## Image commands

Build manually:

```bash
docker build -t auth-service:mvp .
```

List images:

```bash
docker image ls
```

Run the image without Compose for a basic liveness test:

```bash
docker run --rm -d \
  --name auth-mvp \
  -p 5001:5000 \
  -e SECRET_KEY=local-container-secret \
  -e JWT_SECRET_KEY=local-container-jwt-secret-at-least-32-bytes \
  -e DATABASE_URL=sqlite:////tmp/auth.db \
  auth-service:mvp
```

Inspect and stop:

```bash
docker ps
docker logs auth-mvp
curl http://localhost:5001/health/live
docker stop auth-mvp
```

The standalone SQLite command is only an image sanity check. Compose with
PostgreSQL is the supported complete runtime.

## Compose command reference

| Command | Purpose |
|---|---|
| `docker compose up -d --build` | Build and start the stack |
| `docker compose up -d` | Start using existing images |
| `docker compose ps --all` | Show running and completed services |
| `docker compose logs` | Show combined logs |
| `docker compose logs -f web` | Follow web logs |
| `docker compose exec web <command>` | Run a command in the active web container |
| `docker compose exec web flask seed-db` | Run interactive Admin/RBAC seeding |
| `docker compose down` | Remove containers and network, preserving data |
| `docker compose down --volumes` | Also delete the PostgreSQL volume |

## Networking

Host-to-container port mapping:

```text
localhost:5001 → web:5000
```

Container-to-container database connection:

```text
web → db:5432
```

Inside the web container, `localhost` means the web container itself. Compose
provides DNS so hostname `db` resolves to the PostgreSQL container.

## Persistent storage

PostgreSQL stores physical files in the `postgres-data` named volume:

```text
Container removed → data remains
Volume removed    → data is deleted
```

The application image never contains database records.

## Clean-checkout verification

This test proves that the repository has no hidden dependency on an existing
virtual environment, uncommitted file, local database, or cached application
state.

Stop the original stack, then clone into a separate folder:

```bash
docker compose down
cd ..
git clone <repository-url> auth-clean-test
cd auth-clean-test
git switch dev
cp .env.example .env
```

Configure fresh secrets and a fresh Compose database password, then:

```bash
docker compose up -d --build
docker compose ps --all
docker compose exec web flask seed-db
curl http://localhost:5001/health/live
```

Verify login and the expected dashboards in the browser.

Clean up the isolated environment:

```bash
docker compose down --volumes
```

Successful completion proves that another contributor can clone and run the
MVP from committed files alone.

## Published images

GitHub Releases publish multi-platform application images to GitHub Container
Registry:

```text
ghcr.io/<owner>/<repository>:<version>
```

Pull an exact version:

```bash
docker pull ghcr.io/<owner>/<repository>:1.0.0
```

Prefer exact versions over `latest` for deployment because an exact version is
repeatable and can be rolled back deliberately.

The PostgreSQL database is not included in the application image. A deployment
must provide PostgreSQL separately and pass its connection through
`DATABASE_URL`.

## Common issue: port already in use

If port 5000 or 5001 is occupied, change `APP_PORT` in `.env`:

```dotenv
APP_PORT=5002
```

Then use `http://localhost:5002`. The container still listens internally on
port 5000.
