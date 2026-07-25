# Application Setup

## Requirements

- Python with `venv`
- PostgreSQL
- Git

## First-time setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows, activate the environment with:

```text
.venv\Scripts\activate
```

Create a local PostgreSQL database and configure `.env`:

```dotenv
FLASK_DEBUG=true
SECRET_KEY=replace-with-a-strong-random-secret
JWT_SECRET_KEY=replace-with-a-different-strong-random-secret
JWT_ACCESS_TOKEN_MINUTES=15
JWT_REFRESH_TOKEN_DAYS=30
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/auth
```

Never commit `.env`.

Apply migrations:

```bash
flask db upgrade
```

Seed RBAC data and create the first administrator:

```bash
flask seed-db
```

The command interactively asks for the Admin username, email, full name, and a
hidden password with confirmation. Run it before public registration because
new registrations require the seeded Employee role.

Start Flask:

```bash
flask run
```

Open `http://localhost:5000`.

## Useful pages

| Page | Purpose |
|---|---|
| `/login` | Sign in with a username or email |
| `/register` | Create an account with the Employee role |
| `/dashboard` | Resolve and open the dashboard for the current role |
| `/admin` | Admin dashboard |
| `/manager` | Manager dashboard |
| `/accountant` | Accountant dashboard |
| `/employee` | Employee dashboard |

## Health check

```bash
curl http://localhost:5000/health/live
```

## Normal updates

After pulling new migration revisions:

```bash
flask db upgrade
```

This applies only pending migrations and preserves existing data.

## Destructive local reset

> This deletes every application record. Never run it against a production or
> shared database.

```bash
flask db downgrade base && flask db upgrade && flask seed-db
```

The command removes the migrated schema, rebuilds it, and prompts for the
bootstrap administrator again.
