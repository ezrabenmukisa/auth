# Current API Reference

All request and response bodies use JSON unless noted otherwise. Protected
endpoints expect:

```http
Authorization: Bearer <token>
```

## Authentication

| Method | Endpoint | Token | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | None | Register an Employee account |
| POST | `/api/v1/auth/login` | None | Log in with username or email |
| POST | `/api/v1/auth/refresh` | Refresh | Issue a new access token |
| POST | `/api/v1/auth/logout` | Access or refresh | Revoke the shared login session |
| GET | `/api/v1/auth/protected` | Access | Demonstrate protected access |
| GET | `/api/v1/auth/me` | Access | Return the active user and current role |

## Users

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/users/<user_id>` | The authenticated profile owner | View a profile |
| PATCH | `/api/v1/users/<user_id>` | The authenticated profile owner | Update `full_name` |
| GET | `/api/v1/users/` | `users.read` | List/search users with pagination |

List parameters:

- `search` matches username or email.
- `page` is a positive integer.
- `per_page` is from 1 to 100.

## Roles

| Method | Endpoint | Required permission |
|---|---|---|
| POST | `/api/v1/authorization/roles` | `roles.create` |
| GET | `/api/v1/authorization/roles` | `roles.read` |
| GET | `/api/v1/authorization/roles/<role_id>` | `roles.read` |
| PUT | `/api/v1/authorization/roles/<role_id>` | `roles.update` |
| DELETE | `/api/v1/authorization/roles/<role_id>` | `roles.delete` |
| GET | `/api/v1/authorization/users/<user_id>/role` | `roles.read` |
| PUT | `/api/v1/authorization/users/<user_id>/role` | `roles.assign` |

A role assigned to users cannot be deleted until those users are reassigned.

## Permissions

| Method | Endpoint | Required permission |
|---|---|---|
| POST | `/api/v1/authorization/permissions` | `permissions.create` |
| GET | `/api/v1/authorization/permissions` | `permissions.read` |
| GET | `/api/v1/authorization/permissions/<permission_id>` | `permissions.read` |
| PUT | `/api/v1/authorization/permissions/<permission_id>` | `permissions.update` |
| DELETE | `/api/v1/authorization/permissions/<permission_id>` | `permissions.delete` |
| GET | `/api/v1/authorization/roles/<role_id>/permissions` | `permissions.read` |
| POST | `/api/v1/authorization/roles/<role_id>/permissions/<permission_id>` | `permissions.assign` |
| DELETE | `/api/v1/authorization/roles/<role_id>/permissions/<permission_id>` | `permissions.assign` |

## Operations

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health/live` | Confirm that the Flask service is running |

## Security

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/v1/security/forgot-password` | Public | Request a one-time password-reset token |
| POST | `/api/v1/security/reset-password` | Public reset token | Replace a password using an unused, unexpired token |
| POST | `/api/v1/security/users/<user_id>/suspend` | `users.suspend` | Suspend another account |
| POST | `/api/v1/security/users/<user_id>/activate` | `users.suspend` | Reactivate another account |
| GET | `/api/v1/security/audit-logs` | `audit.read` | Review paginated security events |

Password-reset requests always return the same public message, whether or not
the email exists. The raw reset token is not stored in the database or returned
outside the test configuration. A delivery integration is still required to
send reset instructions to users.

## Status-code conventions

- `200` successful request
- `201` resource created
- `400` invalid input or business-rule violation
- `401` missing, invalid, expired, revoked, or inactive authentication
- `403` valid authentication without required access
- `404` resource not found
- `409` duplicate registration identity
- `500` persistence failure
- `503` required RBAC setup is missing during registration
