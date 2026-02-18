"""Microsoft Graph API client for reading Office 365 emails."""

from datetime import datetime, timedelta
from typing import Optional
import requests

from task_tracker.config import Config
from task_tracker.graph_api.auth import refresh_access_token
from task_tracker.models.database import get_auth_token, save_auth_token


class GraphClient:
    """Client for interacting with the Microsoft Graph API."""

    def __init__(self):
        self.base_url = Config.GRAPH_API_BASE
        self._session = requests.Session()

    def _get_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary."""
        token_data = get_auth_token()
        if not token_data:
            return None

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() >= expires_at - timedelta(minutes=5):
            # Token expired or about to expire — refresh it
            try:
                new_tokens = refresh_access_token(token_data["refresh_token"])
                new_expires = datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])
                save_auth_token(
                    access_token=new_tokens["access_token"],
                    refresh_token=new_tokens.get("refresh_token", token_data["refresh_token"]),
                    expires_at=new_expires.isoformat(),
                    user_email=token_data.get("user_email", ""),
                    user_name=token_data.get("user_name", ""),
                )
                return new_tokens["access_token"]
            except requests.RequestException:
                return None

        return token_data["access_token"]

    def _headers(self) -> dict:
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def is_authenticated(self) -> bool:
        """Check if we have a valid auth token."""
        return self._get_access_token() is not None

    def get_user_profile(self) -> Optional[dict]:
        """Get the authenticated user's profile."""
        try:
            resp = self._session.get(
                f"{self.base_url}/me",
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return None

    def get_recent_emails(
        self,
        since: Optional[str] = None,
        max_results: int = 50,
    ) -> list[dict]:
        """Fetch recent emails from the user's inbox.

        Args:
            since: ISO datetime string — only fetch emails received after this time.
            max_results: Maximum number of emails to return.

        Returns:
            List of email message dicts from Graph API.
        """
        params = {
            "$top": max_results,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,bodyPreview,body,from,toRecipients,ccRecipients,receivedDateTime,importance,hasAttachments",
        }

        if since:
            params["$filter"] = f"receivedDateTime ge {since}"

        try:
            resp = self._session.get(
                f"{self.base_url}/me/messages",
                headers=self._headers(),
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("value", [])
        except requests.RequestException:
            return []

    def get_email_by_id(self, email_id: str) -> Optional[dict]:
        """Fetch a single email by its ID."""
        try:
            resp = self._session.get(
                f"{self.base_url}/me/messages/{email_id}",
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return None
