# Authentication and Role-Based Authorization Service

A modular Flask service for user accounts, JWT authentication, session
revocation, roles, permissions, role-specific dashboards, containerized
development, automated CI, versioned container-image delivery, and Railway
deployment.

## Documentation

- [Application setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [Academic project proposal](docs/PROPOSAL.md)

## Current capabilities

- User registration, profiles, search, and pagination
- Password hashing and username-or-email login
- JWT access tokens, refresh tokens, logout, and session revocation
- Roles, permissions, role assignment, and permission enforcement
- Admin, Manager, Accountant, and Employee dashboards
- SQLAlchemy models and Alembic migrations
- Interactive bootstrap-Admin and RBAC seeding
- Docker Compose development environment
- Automated format, lint, test, migration, image-build, publishing, and
  deployment workflows

## Running the project

Use the [application setup guide](docs/setup.md) for the complete Docker
Compose, native Python, database migration, administrator seeding, reset, and
hosted runtime instructions.

The README intentionally contains only the project overview. Operational
commands are maintained in one place in `docs/setup.md`.
