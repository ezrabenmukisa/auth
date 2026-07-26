# Contributing

## Development workflow

1. Pull the latest `dev` branch.
2. Select or create a GitHub issue.
3. Create a focused feature branch from `dev`.
4. Implement the feature through the existing architecture.
5. Add or update tests.
6. Run the complete local quality checks.
7. Push the branch and open a pull request into `dev`.
8. Obtain a review before merging.

## Architecture rules

Feature code follows:

```text
Request → Route → Schema → Service → Model → Database
```

- Routes handle HTTP input and responses.
- Schemas validate and normalize input.
- Services contain business logic and transaction handling.
- Models define persistence.
- Shared extensions come from `app/extensions.py`.
- Blueprints are registered only by the application factory.
- Do not introduce repository classes or unnecessary utility layers.

## Database changes

Generate a migration only when SQLAlchemy models change:

```bash
flask db migrate -m "describe the schema change"
flask db upgrade
```

Review the generated revision before committing it. Never edit or regenerate
another contributor's already-shared migration merely to change its revision
identifier.

After pulling someone else's migration, run:

```bash
flask db upgrade
```

## Required checks

```bash
python -m pip install -r requirements-dev.txt
pytest -v
ruff check .
black --check .
```

When frontend JavaScript changes, also check its syntax:

```bash
node --check app/static/js/<changed-file>.js
```

## Security expectations

- Never commit `.env`.
- Never log or return plaintext passwords, password hashes, or raw JWTs.
- Use application services for writes and roll back failed transactions.
- Add authentication and permission checks to protected operations.
- Test successful, invalid, unauthorized, and forbidden requests.

See [Architecture](architecture.md), [Testing](testing.md), and
[Database and migrations](database.md) for more detail.
