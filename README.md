# Authentication and Role-Based Authorization Service

A modular Flask service for user accounts, JWT authentication, session
revocation, roles, permissions, and role-specific dashboards.

## Documentation

- [Documentation index](docs/README.md)
- [Application setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [Authentication and token lifecycle](docs/authentication.md)
- [Authorization and seeded access](docs/authorization.md)
- [Database and migrations](docs/database.md)
- [Testing and quality checks](docs/testing.md)
- [Contributing](docs/CONTRIBUTE.md)
- [Academic project proposal](docs/PROPOSAL.md)

## Getting Started

After cloning the repository, complete the following setup before you begin development.

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it.

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 2. Install project dependencies

```bash
pip install -r requirements-dev.txt
```

### 3. Create your environment file

Copy the example configuration.

```bash
cp .env.example .env
```

Fill in your local PostgreSQL credentials and application secrets.

### 4. Create the local PostgreSQL database

Create your own PostgreSQL database locally and update the `DATABASE_URL` inside `.env`.

### 5. Apply database migrations

When running Flask directly on your computer, create or update the application
schema using the committed Alembic migrations:

```bash
flask db upgrade
```

This command preserves existing data and applies only migrations that have not
already run. With Docker Compose, a one-off migration service performs this
step automatically before the web service starts.

### 6. Seed roles, permissions, and the first administrator

Run the interactive bootstrap command:

```bash
flask seed-db
```

When using Docker Compose, run it inside the web container:

```bash
docker compose exec web flask seed-db
```

Enter the administrator's username, email, full name, and password when
prompted. Password input is hidden and must be confirmed.

The command creates or synchronizes the Employee, Accountant, Manager, and
Admin roles, their permissions, and the bootstrap administrator. It is
idempotent, so running it again does not create duplicate seed records.

New accounts created through registration receive the Employee role. Therefore,
run `flask seed-db` before accepting registrations.

### 7. Run the application

```bash
python run.py
```

or

```bash
flask run
```

Open the application at:

```text
http://localhost:5000
```

Useful pages:

- `/login` — sign in using a username or email
- `/register` — create an Employee account
- `/dashboard` — redirect to the dashboard for the signed-in user's role

### 8. Verify the health endpoint

```bash
curl http://localhost:5000/health/live
```

### 9. Run quality checks

```bash
pytest -v
ruff check .
black --check .
```

## Resetting the local development database

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

## Authentication token usage

Login at `POST /api/v1/auth/login` with a username or email in the
`identifier` field:

```json
{
  "identifier": "newuser",
  "password": "your-password"
}
```

Send JWTs using `Authorization: Bearer <token>`. The refresh endpoint requires
a refresh token; protected resources require an access token. Logging out with
either token revokes the complete login session, including its paired access
and refresh tokens.


---

## Development Guidelines

Before starting work:

- Pull the latest changes from `develop`.
- Pick or create a GitHub Issue.
- Create a feature branch from `develop`.
- Implement both the feature and its tests.
- Run the test suite before pushing.
- Open a Pull Request into `develop`.
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
