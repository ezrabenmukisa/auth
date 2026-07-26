# Authentication and Role-Based Authorization Service

A modular Flask service for user accounts, JWT authentication, session
revocation, roles, permissions, role-specific dashboards, containerized
development, automated CI, and versioned container-image delivery.

## Documentation

- [Documentation index](docs/README.md)
- [Application setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [Authentication and token lifecycle](docs/authentication.md)
- [Authorization and seeded access](docs/authorization.md)
- [Database and migrations](docs/database.md)
- [Docker and clean-checkout workflow](docs/docker.md)
- [CI/CD](docs/ci-cd.md)
- [Testing and quality checks](docs/testing.md)
- [Contributing](docs/CONTRIBUTE.md)
- [Academic project proposal](docs/PROPOSAL.md)

## Getting Started

Docker Compose is the recommended reproducible setup. It runs Flask, Gunicorn,
PostgreSQL, and migrations without requiring a local Python or PostgreSQL
installation.

### 1. Clone and configure

```bash
git clone <repository-url> auth
cd auth
git switch dev
cp .env.example .env
```

Replace the placeholder secrets and Docker database password in `.env`. Never
commit that file.

### 2. Build and start

```bash
docker compose up -d --build
```

Compose waits for PostgreSQL, runs pending migrations in a one-off container,
then starts Gunicorn.

### 3. Confirm service state

```bash
docker compose ps --all
```

Expected state:

```text
db       Up (healthy)
migrate  Exited (0)
web      Up
```

### 4. Seed the first administrator

```bash
docker compose exec web flask seed-db
```

Enter the Admin username, email, full name, and hidden password when prompted.
The seed is idempotent and also creates the required RBAC mappings.

### 5. Open the application

```text
http://localhost:5001
```

Useful pages:

- `/login` — sign in using a username or email
- `/register` — create an Employee account
- `/dashboard` — redirect to the dashboard for the signed-in user's role

Verify liveness:

```bash
curl http://localhost:5001/health/live
```

### 6. Stop the stack

Preserve the database:

```bash
docker compose down
```

Delete the containers and local Docker database:

```bash
docker compose down --volumes
```

The second command is destructive.

### Native alternative

Running Flask and PostgreSQL directly on the host is still supported. See the
[complete setup guide](docs/setup.md#native-development-alternative).

### Quality checks

```bash
python -m pip install -r requirements-dev.txt
pytest -v
ruff check .
black --check .
```

## Resetting a native development database

> **Warning:** The following command deletes all application data, including
> users, roles, permissions, and revoked-token sessions. Use it only for a local
> development database that is safe to erase.

Downgrade the schema to the Alembic base, rebuild it from the committed
migrations, and run the interactive seed command:

```bash
flask db downgrade base && flask db upgrade && flask seed-db
```

Do not use this reset workflow for a production or shared database.

For normal development updates after pulling new migrations, use only:

```bash
flask db upgrade
```


---

## Development Guidelines

Before starting work:

- Pull the latest changes from `dev`.
- Pick or create a GitHub Issue.
- Create a feature branch from `dev`.
- Implement both the feature and its tests.
- Run the test suite before pushing.
- Open a Pull Request into `dev`.
- Wait for review before merging.

> **Important**
>
> - Never commit `.env`.
> - Never modify another member's feature branch.
> - Never regenerate migrations that already exist in the repository.
> - If new migration files are added by another teammate, pull the latest changes and run `flask db upgrade`.


---

# Project Structure Guide

Every feature in this project follows the same structure to keep the codebase consistent and easy to maintain.

```
app/
├── modules/
│   ├── authentication/
│   ├── authorization/
│   ├── security/
│   └── users/
│       ├── routes.py
│       ├── services.py
│       └── schemas.py
```

## `routes.py` — HTTP Endpoints

Routes receive HTTP requests from clients.

Responsibilities:

- Define API endpoints
- Read request data
- Validate input using schemas
- Call service functions
- Return HTTP responses

Routes should **not** contain business logic or database operations.

Example:

```python
@users_bp.post("/")
def register():
    ...
```

---

## `services.py` — Business Logic

Services contain the application's business rules.

Responsibilities:

- Perform validation that depends on business rules
- Query and modify the database
- Call helper functions
- Raise application errors
- Return results back to routes

Services should not define HTTP endpoints.

---

## `schemas.py` — Request and Response Validation

Schemas describe what data is accepted and returned.

Responsibilities:

- Validate incoming JSON
- Serialize responses
- Reject invalid data before it reaches the service layer

Every endpoint that accepts data should use an appropriate schema.

---

## `models/`

Models define the database tables using SQLAlchemy.

Responsibilities:

- Table definitions
- Relationships
- Constraints

Models should not contain HTTP logic.

---

## `extensions.py`

Shared Flask extensions are initialized here.

Examples include:

- SQLAlchemy
- Flask-Migrate
- JWT Manager

Never create new instances of these extensions inside feature modules.

Use the shared objects imported from `extensions.py`.

---

## `config.py`

Contains application configuration.

Different configurations can be used for:

- Development
- Testing
- Production

Do not hardcode secrets or database credentials.

Always use environment variables.

---

## Blueprints

Each module exposes one Blueprint.

Example:

```python
users_bp
```

Blueprints are registered only inside `create_app()`.

Do not register blueprints anywhere else.

---

## Tests

Every feature must include automated tests.

Examples:

```
tests/
    test_users.py
    test_authentication.py
    test_authorization.py
```

Every new endpoint should include tests for:

- Successful requests
- Invalid input
- Unauthorized access (where applicable)
- Failure cases

---

## Database Migrations

Only generate a migration when you modify SQLAlchemy models.

Workflow:

```
Modify models
      ↓
flask db migrate
      ↓
flask db upgrade
      ↓
Commit migration files
```

Other team members should **not** regenerate the same migration.

Instead:

```
git pull
flask db upgrade
```

---

## Decorators

Decorators add reusable behaviour to endpoints.

Examples include:

- Authentication
- Permission checks
- Logging
- Rate limiting

Decorators should contain reusable logic shared by multiple routes.

Avoid duplicating the same authorization checks across different endpoints.

---

## General Rule

Business logic should always follow this flow:

```
HTTP Request
      ↓
Route
      ↓
Schema
      ↓
Service
      ↓
Model
      ↓
Database
```

Never skip layers without a good reason.
---
