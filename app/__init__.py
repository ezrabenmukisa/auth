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
        from app import models  # noqa: F401

    from app.authentication import authentication_bp
    from app.authentication.services import is_session_revoked
    from app.cli.seed import seed_db
    from app.health import health_bp
    from app.users import users_bp

    app.register_blueprint(authentication_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)
    app.cli.add_command(seed_db)

    @jwt.token_in_blocklist_loader
    def token_in_blocklist(_jwt_header, jwt_payload):
        """Reject every access or refresh token from a revoked session."""
        return is_session_revoked(jwt_payload)

    return app
