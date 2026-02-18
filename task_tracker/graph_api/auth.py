"""OAuth2 authentication flow for Microsoft Graph API."""

import urllib.parse
import requests
from task_tracker.config import Config, get_azure_credentials


def get_auth_url(state: str = "") -> str:
    """Generate the Microsoft OAuth2 authorization URL."""
    creds = get_azure_credentials()
    authority = f"https://login.microsoftonline.com/{creds['tenant_id']}"
    params = {
        "client_id": creds["client_id"],
        "response_type": "code",
        "redirect_uri": creds["redirect_uri"],
        "response_mode": "query",
        "scope": " ".join(Config.SCOPES),
        "state": state,
    }
    return f"{authority}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(auth_code: str) -> dict:
    """Exchange an authorization code for access and refresh tokens.

    Returns dict with: access_token, refresh_token, expires_in, token_type
    """
    creds = get_azure_credentials()
    authority = f"https://login.microsoftonline.com/{creds['tenant_id']}"
    token_url = f"{authority}/oauth2/v2.0/token"
    data = {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": creds["redirect_uri"],
        "scope": " ".join(Config.SCOPES),
    }
    resp = requests.post(token_url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Use a refresh token to get a new access token.

    Returns dict with: access_token, refresh_token, expires_in, token_type
    """
    creds = get_azure_credentials()
    authority = f"https://login.microsoftonline.com/{creds['tenant_id']}"
    token_url = f"{authority}/oauth2/v2.0/token"
    data = {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": " ".join(Config.SCOPES),
    }
    resp = requests.post(token_url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()
