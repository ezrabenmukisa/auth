"""Development database seed command."""

import click
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db


class SeedError(Exception):
    """Raised when development seed work cannot complete safely."""


def seed_development_data() -> int:
    """Run the seed transaction without creating incomplete users."""
    try:
        with db.session.begin():
            return 0
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise SeedError("Database seeding failed.") from exc


@click.command("seed-db")
def seed_db():
    """Run explicit, development-only database seeding."""
    seed_development_data()
    click.echo("Database seed command is available.")
    click.echo("No users were seeded because password hashing is not yet implemented.")
