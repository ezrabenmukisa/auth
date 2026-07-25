# Authentication and Token Lifecycle

## Registration

```text
Authentication route
    → Authentication schema
    → Werkzeug password hashing
    → User creation service
    → User model
    → Database
```

`POST /api/v1/auth/register` accepts username, email, password, and an optional
full name. The Authentication module removes the plaintext password from user
data, hashes it, and passes only `password_hash` to User Management.

Registration finds the Employee role by name. If RBAC seed data is missing, it
returns a setup/configuration error instead of assuming a database role ID.

The registration page includes password confirmation as a browser-side UX
check. `confirm_password` is not sent to the API or stored.

## Login

`POST /api/v1/auth/login` accepts:

```json
{
  "identifier": "username-or-email",
  "password": "account-password"
}
```

Username and email login use the same generic invalid-credentials response.
Inactive users cannot log in.

Successful login returns access and refresh tokens. Both contain:

- The User ID as the JWT identity
- A shared session ID (`sid`)
- A shared session expiration claim (`session_expires_at`)

## Access tokens

Access tokens authorize normal protected API requests. The demonstration
endpoint is `GET /api/v1/auth/protected`.

`GET /api/v1/auth/me` also verifies that the represented user still exists and
is active before returning public account and role information.

## Refresh tokens

`POST /api/v1/auth/refresh` accepts only a refresh token. A refreshed access
token keeps the original session ID and shared expiration.

Its expiration is the smaller of:

- The configured access-token lifetime
- The remaining shared-session lifetime

This prevents refreshed access tokens from outliving their login session.

## Logout and revocation

`POST /api/v1/auth/logout` accepts either an access or refresh token. It stores
the shared session ID and expiration in `revoked_tokens`; raw JWTs are never
stored.

Once a session is revoked, both its access and refresh tokens are rejected.
Repeated revocation is idempotent and creates only one database record.

## Expiration configuration

```dotenv
JWT_ACCESS_TOKEN_MINUTES=15
JWT_REFRESH_TOKEN_DAYS=30
```

Changing these values affects newly issued sessions.
