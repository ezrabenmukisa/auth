# Database and Migrations

## Current tables

| Table | Purpose |
|---|---|
| `users` | Identity, profile, password hash, status, timestamps, and assigned role |
| `roles` | Named RBAC roles |
| `permissions` | Named authorization capabilities |
| `role_permissions` | Many-to-many Role-to-Permission mapping |
| `revoked_tokens` | Revoked JWT session IDs and expiration data |
| `alembic_version` | Current Alembic migration revision |

Raw passwords and raw JWTs are never stored.

## Migration chain

The committed revisions run in this order:

```text
6c6bc1946a69  Initial users table
    ↓
0174c045dcb9  Revoked-token sessions
    ↓
5b03f5004cc0  RBAC models and User role assignment
```

The RBAC migration safely handles users that already exist before enforcing the
non-null User role relationship.

## Applying migrations

When running Flask directly:

```bash
flask db upgrade
```

Alembic reads `alembic_version` and applies only missing revisions.
Running the command again does not drop tables or recreate existing data.

With Docker Compose, the `migrate` service runs this command automatically:

```text
db healthy
    → migrate runs flask db upgrade
    → migrate exits successfully
    → web starts Gunicorn
```

Run the normal Compose command:

```bash
docker compose up -d --build
```

The Dockerfile remains responsible only for starting Gunicorn. Keeping
migrations in a one-off service prevents every web replica from attempting the
same migration.

## Creating a migration

Only create a revision after changing SQLAlchemy models:

```bash
flask db migrate -m "describe the schema change"
```

Review both `upgrade()` and `downgrade()` before running:

```bash
flask db upgrade
```

## Local reset

> This operation permanently deletes all migrated application data.

```bash
flask db downgrade base && flask db upgrade && flask seed-db
```

Use it only against a disposable local development database.

## Tests

Migration tests exercise Alembic upgrades on fresh SQLite databases. They do
not substitute `db.create_all()` for migration-path verification.
