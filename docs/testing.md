# Testing and Quality Checks

## Full verification

Activate the virtual environment, then run:

```bash
python -m pip install -r requirements-dev.txt
pytest -v
ruff check .
black --check .
```

`requirements.txt` contains only application runtime dependencies and is used
by the Docker image. `requirements-dev.txt` includes the runtime file and adds
Black, Pytest, and Ruff for contributors and CI.

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

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests targeting `dev` or
`main`. It can also be started manually from the Actions tab.

The workflow contains four independent jobs:

| Job | Verification |
|---|---|
| Format and lint | `black --check .` and `ruff check .` |
| Test application | Complete Pytest suite with `TestConfig` |
| Verify PostgreSQL migrations | Upgrade a fresh PostgreSQL 17 service through Alembic |
| Build Docker image | Build the runtime image without publishing it |

CI uses disposable GitHub-hosted runners and test-only credentials. It does not
read the local `.env`, publish an image, or deploy the application.

See [CI/CD](ci-cd.md) for workflow concepts, local equivalents, and the planned
boundary for continuous delivery.
