"""Flask application factory for the Office 365 Task Tracker."""

from datetime import datetime

from flask import Flask, redirect, url_for, request

from task_tracker.config import Config
from task_tracker.models.database import init_db, is_setup_complete
from task_tracker.routes.auth_routes import auth_bp
from task_tracker.routes.dashboard_routes import dashboard_bp
from task_tracker.routes.sync_routes import sync_bp
from task_tracker.routes.setup_routes import setup_bp


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
    app.register_blueprint(setup_bp)

    # Redirect to setup wizard if not configured yet
    @app.before_request
    def check_setup():
        # Allow setup routes, static files, and auth callback through
        allowed_prefixes = ("/setup", "/static", "/auth/callback")
        if any(request.path.startswith(p) for p in allowed_prefixes):
            return
        if not is_setup_complete():
            return redirect(url_for("setup.index"))

    # Template helpers
    @app.template_global()
    def now_iso():
        return datetime.utcnow().date().isoformat()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=Config.DEBUG, port=5000)
