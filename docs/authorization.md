# Authorization and RBAC

## Data model

Each User has one Role. Roles have many Permissions through the
`role_permissions` association table.

Permission-protected routes first validate the JWT and active user, then check
whether the user's current role contains the required permission:

- Authentication failure returns `401`.
- Missing permission returns `403`.
- A user without a role has no permissions.

## Seeded roles

`flask seed-db` creates and synchronizes these exact mappings:

| Role | Permissions |
|---|---|
| Employee | None |
| Accountant | `permissions.read` |
| Manager | `roles.read`, `permissions.read` |
| Admin | Every seeded authorization permission |

The seeded permissions are:

- `roles.create`
- `roles.read`
- `roles.update`
- `roles.delete`
- `roles.assign`
- `permissions.create`
- `permissions.read`
- `permissions.update`
- `permissions.delete`
- `permissions.assign`

The command also creates the bootstrap Admin through the Authentication
registration and password-hashing flow. It is safe to run repeatedly with the
same administrator details.

## Registration role

Normal registration explicitly looks up Employee by name and assigns it to the
new account. No hard-coded role ID is used.

## Dashboards

- Admin can manage people, roles, permissions, and role-permission mappings.
- Manager can view roles and permissions.
- Accountant can view permissions.
- Employee sees account and profile information.

The People view prevents the logged-in Admin from reassigning their own role in
the interface. Other users can be assigned roles by an Admin.

## Current limitations

The current system does not implement invitations, multi-role users, account
deletion, last-Admin enforcement, or audit logging. These should not be implied
by the existing RBAC screens.
