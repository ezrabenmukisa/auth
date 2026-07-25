# Documentation

This directory contains the detailed documentation for the current
implementation.

## Guides

| Document | Purpose |
|---|---|
| [Setup](setup.md) | Install, configure, migrate, seed, run, and reset the application |
| [Architecture](architecture.md) | Application factory, modules, and request flow |
| [API reference](api.md) | Current HTTP endpoints and access requirements |
| [Authentication](authentication.md) | Registration, login, JWT refresh, logout, and revocation |
| [Authorization](authorization.md) | Roles, permissions, seeded mappings, and dashboards |
| [Database](database.md) | Models, migration chain, and safe migration workflows |
| [Testing](testing.md) | Fixtures, test organization, quality commands, and CI |
| [Contributing](CONTRIBUTE.md) | Team workflow and implementation rules |
| [Project proposal](PROPOSAL.md) | Original academic scope and planned deliverables |

## Current versus proposed functionality

The implementation currently includes:

- User registration, login, and profile-name updates
- Werkzeug password hashing
- JWT access and refresh tokens
- Shared-session logout and token revocation
- Roles, permissions, user-role assignment, and permission enforcement
- Interactive bootstrap-Admin seeding
- User-facing login, registration, profile, and role-specific dashboard pages
- Liveness endpoint, migrations, and automated tests

The proposal also describes later work such as password recovery, password
changes, audit logging, readiness checks, OpenAPI documentation, image
publishing, and deployment. Those items must not be treated as implemented
until the corresponding code is merged.
