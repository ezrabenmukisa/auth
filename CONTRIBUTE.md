
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
pip install -r requirements.txt
```

### 3. Create your environment file

Copy the example configuration.

```bash
cp .env.example .env
```

Fill in your local PostgreSQL credentials and application secrets.

### 4. Create your local database

Create your own PostgreSQL database locally and update the `DATABASE_URL` inside `.env`.

### 5. Apply database migrations

Whenever migration files exist, run:

```bash
flask db upgrade
```

### 6. Run the application

```bash
python run.py
```

or

```bash
flask run
```

### 7. Run the tests

```bash
pytest
```


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
├── users/
│   ├── routes.py
│   ├── services.py
│   └── schemas.py
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