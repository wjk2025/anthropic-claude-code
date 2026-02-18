"""Configuration for the Office 365 Task Tracker."""

import os


class Config:
    """Application configuration loaded from environment variables."""

    # Microsoft Azure AD / Entra ID App Registration
    CLIENT_ID = os.environ.get("O365_CLIENT_ID", "")
    CLIENT_SECRET = os.environ.get("O365_CLIENT_SECRET", "")
    TENANT_ID = os.environ.get("O365_TENANT_ID", "")
    REDIRECT_URI = os.environ.get("O365_REDIRECT_URI", "http://localhost:5000/auth/callback")

    # Microsoft Graph API
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
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
