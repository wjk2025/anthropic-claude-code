"""Flask application factory for the Office 365 Task Tracker."""

from datetime import datetime

from flask import Flask

from task_tracker.config import Config
from task_tracker.models.database import init_db
from task_tracker.routes.auth_routes import auth_bp
from task_tracker.routes.dashboard_routes import dashboard_bp
from task_tracker.routes.sync_routes import sync_bp


def create_app(config: Config | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.secret_key = Config.SECRET_KEY

    # Initialize the database
    init_db(Config.DATABASE_PATH)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(sync_bp)

    # Template helpers
    @app.template_global()
    def now_iso():
        return datetime.utcnow().date().isoformat()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=Config.DEBUG, port=5000)
