"""Configuration for the Office 365 Task Tracker."""

import os


class Config:
    """Application configuration loaded from environment variables."""

    # Microsoft Graph API (static)
    SCOPES = ["Mail.Read", "Mail.ReadBasic", "User.Read"]
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    # Flask
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", os.urandom(32).hex())
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # Database
    DATABASE_PATH = os.environ.get("TASK_DB_PATH", "task_tracker.db")

    # Polling interval for checking new emails (in seconds)
    POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))

    # Maximum emails to fetch per poll
    MAX_EMAILS_PER_POLL = int(os.environ.get("MAX_EMAILS_PER_POLL", "50"))


def get_azure_credentials() -> dict:
    """Get Azure AD credentials from the database, falling back to env vars."""
    from task_tracker.models.database import get_app_settings

    settings = get_app_settings()
    if settings and settings.get("setup_complete"):
        return {
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "tenant_id": settings["tenant_id"],
            "redirect_uri": settings["redirect_uri"],
        }

    # Fallback to environment variables
    return {
        "client_id": os.environ.get("O365_CLIENT_ID", ""),
        "client_secret": os.environ.get("O365_CLIENT_SECRET", ""),
        "tenant_id": os.environ.get("O365_TENANT_ID", ""),
        "redirect_uri": os.environ.get("O365_REDIRECT_URI", "http://localhost:5000/auth/callback"),
    }
