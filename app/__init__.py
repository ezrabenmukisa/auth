"""Flask application factory."""

from flask import Flask

from app.config import Config
from app.extensions import db, jwt, migrate


def create_app(config_class=Config):
    """Create and configure an application instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    with app.app_context():
        from app import models

    from app.health import health_bp
    from app.users import users_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)

    from app.commands import seed_db
    app.cli.add_command(seed_db)
    return app
