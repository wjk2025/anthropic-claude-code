"""OAuth2 authentication flow for Microsoft Graph API."""

import urllib.parse
import requests
from task_tracker.config import Config


def get_auth_url(state: str = "") -> str:
    """Generate the Microsoft OAuth2 authorization URL."""
    params = {
        "client_id": Config.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": Config.REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(Config.SCOPES),
        "state": state,
    }
    return f"{Config.AUTHORITY}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(auth_code: str) -> dict:
    """Exchange an authorization code for access and refresh tokens.

    Returns dict with: access_token, refresh_token, expires_in, token_type
    """
    token_url = f"{Config.AUTHORITY}/oauth2/v2.0/token"
    data = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": Config.REDIRECT_URI,
        "scope": " ".join(Config.SCOPES),
    }
    resp = requests.post(token_url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Use a refresh token to get a new access token.

    Returns dict with: access_token, refresh_token, expires_in, token_type
    """
    token_url = f"{Config.AUTHORITY}/oauth2/v2.0/token"
    data = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": " ".join(Config.SCOPES),
    }
    resp = requests.post(token_url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()
