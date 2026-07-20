# PROJECT PROPOSAL

## Design and Implementation of an Authentication and Role-Based Authorization Microservice Using Flask

**Course:** BSE2301 Software Engineering  
**Project category:** Microservice Architecture (Flask)  
**Group:** Group J - Day Programme  
**Team size:** Five members  
**Project period:** 17–30 July 2026

## 1. Executive Summary

Modern applications need a secure way to identify users and determine which resources each user may access. Reimplementing these controls in every application duplicates work, increases maintenance costs, and can create inconsistent security practices.

This project proposes a standalone Authentication and Role-Based Authorization Microservice built with Flask. It will provide reusable REST API endpoints for registration, login, token refresh, logout, password management, user administration, role assignment, permission management, and access control.

The service will use JSON Web Tokens (JWT) for authentication, secure password hashing, Role-Based Access Control (RBAC), PostgreSQL for persistent storage, and audit logs for security events. It will be containerized with Docker and orchestrated with Docker Compose. Automated testing, API documentation, code-quality checks, and a GitHub Actions continuous integration pipeline will form its core DevOps tooling.

## 2. Background

University portals, healthcare platforms, e-commerce systems, financial applications, and internal business systems all require authentication and authorization. When each application implements these capabilities independently, developers repeatedly solve the same problem and may introduce inconsistent or weak controls.

A dedicated microservice centralizes identity and access management. Client applications send authentication requests to the service and rely on it to issue tokens and enforce access rules. This makes the capability reusable without requiring the team to build an entire surrounding business application.

## 3. Problem Statement

Many small and medium-sized systems implement authentication separately inside each application. This causes duplicated code, inconsistent password security, unclear authorization rules, limited security auditing, and greater maintenance effort.

There is therefore a need for an independently deployable service that securely manages user identities, tokens, roles, and permissions through a consistent REST API.

## 4. Proposed Solution

The proposed solution is a Flask-based Authentication and Role-Based Authorization Microservice. Users will be able to register, log in, obtain access and refresh tokens, refresh access, log out, view and update their profiles, and manage passwords.

Administrators will be able to manage user status, roles, permissions, and audit records. Protected endpoints will require both a valid token and the appropriate permission. A small administration interface may be included as a demonstration client, but the REST API will remain the main product.

## 5. Project Aim

To design and implement a secure, reusable, containerized, and independently deployable Authentication and Role-Based Authorization Microservice using Flask and PostgreSQL.

## 6. Specific Objectives

The project will:

1. Design a modular Flask REST API for identity and access management.
2. Implement secure user registration and login.
3. Store passwords using secure one-way hashing.
4. Generate JWT access and refresh tokens.
5. Implement token refresh, revocation, and logout.
6. Implement account activation and suspension.
7. Implement roles and permissions using RBAC.
8. Protect endpoints according to assigned permissions.
9. Provide profile and password-management functions.
10. Record important security activities in audit logs.
11. Store application data in PostgreSQL.
12. Document the API using OpenAPI/Swagger.
13. Implement automated unit and integration tests.
14. Containerize the service using Docker.
15. Orchestrate the application and database using Docker Compose.
16. Automate quality checks and tests using GitHub Actions.
17. Document, demonstrate, and evaluate the completed service.

## 7. Project Scope

### 7.1 Included in the first release

- User registration and login
- Secure password hashing
- JWT access and refresh tokens
- Token refresh, revocation, and logout
- User profile viewing and updating
- Password changing and password-reset workflow
- User activation and suspension
- Roles, permissions, and user-role assignment
- Permission-protected endpoints
- Administrative user management
- Security audit logs
- Liveness and readiness endpoints
- PostgreSQL persistence and migrations
- OpenAPI/Swagger documentation
- Automated tests and code-quality checks
- Docker containerization
- Docker Compose orchestration
- GitHub Actions continuous integration
- A simple demonstration or administration interface, if time permits

### 7.2 Outside the first release

- Social login with Google, Facebook, or Microsoft
- Biometric or SMS-based authentication
- Full enterprise Single Sign-On
- OAuth 2.0/OpenID Connect provider functionality
- Kubernetes deployment
- Advanced intrusion detection



## 8. Stakeholders and Users

- **End users:** register, log in, manage their profiles, and access permitted resources.
- **Administrators:** manage accounts, roles, permissions, and audit records.
- **Application developers:** integrate other applications through the REST API.
- **Academic stakeholders:** Group J members, lecturers, and project supervisors.

## 9. Functional Requirements

### 9.1 Registration and account management

The service shall validate registration data, reject duplicate usernames or emails, enforce a password policy, hash passwords before storage, assign a default role, and allow authorized profile changes.

### 9.2 Authentication and token lifecycle

The service shall authenticate valid users, reject invalid or disabled accounts, issue time-limited access and refresh tokens, refresh access tokens, revoke tokens at logout, and reject expired, malformed, or revoked tokens.

### 9.3 Password management

Users shall be able to change their passwords after confirming the current password. The service shall also support limited-duration, single-use password-reset tokens without revealing whether an email address is registered.

### 9.4 Role-Based Access Control

Administrators shall be able to create roles and permissions, connect permissions to roles, assign roles to users, and remove assignments. Protected endpoints shall deny access when the required permission is missing.

Initial roles will include `Admin`, `Manager`, and `User`. Example permissions include `users.read`, `users.update`, `users.disable`, `roles.read`, `roles.manage`, and `audit.read`.

### 9.5 Administrative functions

Authorized administrators shall be able to list and search users, view individual accounts, activate or suspend users, assign and remove roles, and inspect audit events.

### 9.6 Auditing and monitoring

The service shall record registration, login success or failure, logout, password changes, password resets, role changes, account-status changes, and unauthorized access attempts. Passwords and raw tokens shall never be logged.

It shall also expose liveness and readiness endpoints and produce consistent application logs and error responses.

## 10. Non-Functional Requirements

### Security

- Passwords shall never be stored as plain text.
- Signing keys and database credentials shall use environment variables.
- Secret files shall not be committed to GitHub.
- Inputs shall be validated and protected endpoints shall enforce permissions.
- Sensitive values shall not appear in API responses or logs.

### Reliability

- Invalid requests shall not crash the service.
- Database changes shall use transactions where appropriate.
- Automated tests shall protect important behaviour from regression.

### Performance and scalability

- Commonly queried database fields shall be indexed.
- Collection endpoints shall use pagination.
- The API shall remain stateless where practical so additional instances can be introduced later.

### Maintainability and portability

- The application shall use clearly separated modules.
- Schema changes shall use migrations.
- Code shall follow shared formatting and naming rules.
- Docker shall provide a consistent environment across team computers.

## 11. Major System Modules

1. **Application Core:** configuration, extension initialization, blueprints, errors, and logging.
2. **User Management:** registration, profiles, account status, search, and pagination.
3. **Authentication:** login, JWT generation, refresh, logout, validation, and revocation.
4. **Authorization:** roles, permissions, assignments, and protected endpoints.
5. **Password Recovery:** reset requests, expiring tokens, and reset completion.
6. **Audit and Monitoring:** security events, logs, health, and readiness checks.
7. **Administration Interface:** a simple client for user and role administration.
8. **Documentation and Testing:** OpenAPI, unit tests, integration tests, and test data.
9. **DevOps and Deployment:** Docker, Compose, CI, environment configuration, and release procedures.

## 12. Proposed Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| Framework | Flask with Blueprints |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy and Flask-Migrate/Alembic |
| Authentication | Flask-JWT-Extended |
| Password security | Argon2 or Werkzeug security utilities |
| Validation | Marshmallow or Pydantic |
| API documentation | OpenAPI/Swagger |
| Testing | Pytest and pytest-cov |
| Code quality | Ruff and Black |
| Containerization | Docker |
| Orchestration | Docker Compose |
| Continuous integration | GitHub Actions |
| Version control | Git and GitHub |

## 13. DevOps, Containerization, and Orchestration

GitHub will provide source control, issues, branches, pull requests, reviews, releases, and contribution evidence. GitHub Actions will install dependencies, check formatting, run linting, start a PostgreSQL test service, apply migrations, run tests, and build the Docker image.

A Dockerfile will package the Flask service and its dependencies. Docker Compose will orchestrate the `auth-api` and `postgres` containers. An optional Mailpit container may be used to demonstrate password-reset emails without a paid provider.

Configuration and secrets will be supplied through environment variables. A safe `.env.example` will be committed, while the real `.env` will remain ignored.

## 14. Testing and Evaluation

Unit tests will cover password utilities, validation, token helpers, authorization checks, and model behaviour. Integration tests will cover registration, login, token refresh, logout, password reset, role assignment, protected endpoints, account suspension, and database health.

The final acceptance demonstration will show:

1. Registering a user.
2. Logging in and receiving tokens.
3. Accessing a user-level endpoint.
4. Being denied access to an administrator endpoint.
5. Assigning an administrative role.
6. Accessing the endpoint after authorization.
7. Refreshing an access token.
8. Logging out and demonstrating token revocation.
9. Viewing the corresponding audit events.

## 15. Work Plan

| Period | Main outcome |
|---|---|
| Days 1 | Requirements, repository, architecture, Flask skeleton, PostgreSQL, and initial Compose setup |
| Days 2 | Database models, migrations, registration, profiles, validation, and tests |
| Days 3-4 | Login, access tokens, refresh tokens, protected routes, logout, and revocation |
| Days 5-6 | Roles, permissions, assignments, authorization tests, and administration functions |
| Days 7-8 | Password recovery, account controls, audit logging, and health checks |
| Days 9 | Docker completion, CI, integration tests, Swagger documentation, and deployment guide |
| Days 10 | Final QA, report, screenshots, release, rehearsal, and presentation |

## 16. Anticipated Risks and Mitigation

| Risk | Mitigation |
|---|---|
| Scope becomes too large | Keep optional features outside the required release |
| Merge conflicts | Use small feature branches and frequent pull requests |
| Unequal participation | Assign GitHub issues and require reviews and tests |
| Security mistakes | Use maintained libraries and test failure cases |
| Environment differences | Use Docker Compose and database migrations |
| Secrets reach GitHub | Use `.env`, `.gitignore`, review, and secret scanning |
| Late integration failures | Integrate continuously instead of waiting for the final days |
| Presentation environment fails | Rehearse from a clean setup and keep backup screenshots |

## 17. Expected Deliverables

- Flask authentication and authorization microservice
- PostgreSQL database and migrations
- Documented REST API
- Role-Based Access Control
- Password management and audit logging
- Automated test suite
- Dockerfile and Docker Compose configuration
- GitHub Actions workflow
- Administration or demonstration client
- Project report, screenshots, presentation, and GitHub source link

## 18. Conclusion

The proposed Authentication and Role-Based Authorization Microservice provides a focused, reusable, and realistic business capability. It can operate independently while allowing other applications to integrate through a REST API.

The project is sufficiently modular for five members and achievable within two weeks when optional enterprise features remain outside the first release. Flask, PostgreSQL, JWT, RBAC, automated testing, GitHub Actions, Docker, and Docker Compose directly address the assignment requirement to build a microservice with full DevOps tooling, containerization, and orchestration.
