# Continuous Integration and Delivery

## Terms

- Continuous Integration (CI) automatically verifies changes before or after
  integration.
- Continuous Delivery prepares a verified, versioned release artifact for
  deployment.
- Continuous Deployment automatically releases verified changes to a live
  environment.
- GitHub Actions is the automation platform used to implement these workflows.

## Current CI workflow

The workflow is stored at `.github/workflows/ci.yml`.

It runs:

- On pushes to `dev` and `main`
- On pull requests targeting `dev` and `main`
- Manually through `workflow_dispatch`

GitHub creates disposable Ubuntu runners that do not contain the developer's
virtual environment, `.env`, or local database.

## Jobs

Four independent jobs can run in parallel:

| Job | Commands and purpose |
|---|---|
| Format and lint | Installs development dependencies, then runs `black --check .` and `ruff check .` |
| Test application | Runs the complete Pytest suite using `TestConfig` |
| Verify PostgreSQL migrations | Starts PostgreSQL 17, runs `flask db upgrade`, and reports the applied Alembic revision |
| Build Docker image | Runs `docker build --tag auth-service:ci .` |

All jobs must pass before the change should be merged.

## Local equivalents

Before pushing:

```bash
python -m pip install -r requirements-dev.txt
black --check .
ruff check .
pytest -v
docker compose run --rm migrate
docker build --tag auth-service:ci .
```

If Ruff reports safe import or formatting fixes:

```bash
ruff check --fix .
black .
ruff check .
black --check .
pytest -v
```

Review automatic changes before committing.

## Credentials

CI uses disposable test credentials for its temporary PostgreSQL service.
It does not read `.env` or use local developer secrets.

Future publishing or deployment credentials must be stored in GitHub Secrets,
not committed in workflow YAML.

## Continuous delivery to GHCR

`.github/workflows/publish.yml` runs only when a GitHub Release is published.
This creates a deliberate human approval point after CI and review.

Release flow:

```text
CI passes on the pull request
    → changes merge to main
    → maintainer publishes a semantic GitHub Release
    → workflow builds AMD64 and ARM64 images
    → workflow publishes versioned tags to GHCR
```

The release tag must use semantic versioning, such as `v1.0.0`.

For repository `<owner>/<repository>` and release `v1.2.3`, the workflow
publishes:

```text
ghcr.io/<owner>/<repository>:1.2.3
ghcr.io/<owner>/<repository>:1.2
ghcr.io/<owner>/<repository>:sha-<commit>
ghcr.io/<owner>/<repository>:latest
```

Prereleases do not update `latest`.

### Registry authentication

The workflow requests only:

```yaml
permissions:
  contents: read
  packages: write
```

It logs into `ghcr.io` with the workflow's temporary `GITHUB_TOKEN`. No Docker
Hub account or committed registry password is required.

### Publishing the first release

Before publishing:

1. Confirm the code is merged into `main`.
2. Confirm CI is green on that commit.
3. Open GitHub's Releases page.
4. Select **Draft a new release**.
5. Create a new tag such as `v1.0.0` from `main`.
6. Add a release title and notes.
7. Select **Publish release**.

The **Publish container image** workflow then starts in the Actions tab.

### Pulling a published image

For a public package:

```bash
docker pull ghcr.io/<owner>/<repository>:1.0.0
```

For a private package, first authenticate with a GitHub personal access token
that can read packages:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
docker pull ghcr.io/<owner>/<repository>:1.0.0
```

Run a specific published version:

```bash
docker run --rm -p 5001:5000 \
  -e SECRET_KEY=<runtime-secret> \
  -e JWT_SECRET_KEY=<runtime-jwt-secret> \
  -e DATABASE_URL=<runtime-database-url> \
  ghcr.io/<owner>/<repository>:1.0.0
```

Runtime secrets and database data remain outside the image.

## Current deployment boundary

Continuous delivery now publishes the versioned application artifact, but it
does not deploy to a hosting platform.

Deployment should be designed only after choosing a host and defining:

- Runtime secret management
- PostgreSQL hosting and backups
- Migration execution
- Health checks
- Rollback strategy
- Domain name and HTTPS
