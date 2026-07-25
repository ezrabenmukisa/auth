# Testing and Quality Checks

## Full verification

Activate the virtual environment, then run:

```bash
pytest -v
ruff check .
black --check .
```

## Shared fixtures

`tests/conftest.py` creates the Flask application with `TestConfig`. Each test
gets:

- A Flask application configured for testing
- An in-memory SQLite database
- The schema created before the test
- Database cleanup after the test
- A shared Flask test client

Tests call `app.test_client()` through the `client` fixture. No live server is
required.

## Test organization

| File | Coverage |
|---|---|
| `test_health.py` | Liveness endpoint |
| `test_users.py` | User creation, profiles, validation, search, and pagination |
| `test_authentication.py` | Registration, login, JWT types, refresh, logout, expiry, and revocation |
| `test_authorization.py` | Roles, permissions, assignments, and allowed/denied access |
| `test_seed.py` | Interactive Admin seed and idempotent RBAC mappings |
| `test_migrations.py` | Actual Alembic upgrade path and resulting schema |
| `test_ui.py` | Public pages, dashboards, current-user data, profile integration, and form controls |

## Focused tests

Examples:

```bash
pytest -v tests/test_authentication.py
pytest -v tests/test_authorization.py
pytest -v tests/test_migrations.py
```

## Frontend syntax

When changing JavaScript:

```bash
node --check app/static/js/session.js
node --check app/static/js/login.js
node --check app/static/js/register.js
node --check app/static/js/dashboard.js
```

Browser behavior still requires manual testing because `node --check` verifies
syntax rather than DOM interaction.
