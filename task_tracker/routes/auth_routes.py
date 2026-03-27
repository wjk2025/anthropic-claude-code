"""Authentication routes for Office 365 OAuth2 flow."""

from datetime import datetime, timedelta
from flask import Blueprint, redirect, request, session, url_for, flash

from task_tracker.graph_api.auth import get_auth_url, exchange_code_for_token
from task_tracker.graph_api.client import GraphClient
from task_tracker.models.database import save_auth_token, get_auth_token, clear_auth_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login")
def login():
    """Start the OAuth2 login flow."""
    state = datetime.utcnow().isoformat()
    session["oauth_state"] = state
    return redirect(get_auth_url(state=state))


@auth_bp.route("/callback")
def callback():
    """Handle the OAuth2 callback from Microsoft."""
    error = request.args.get("error")
    if error:
        flash(f"Authentication failed: {request.args.get('error_description', error)}", "error")
        return redirect(url_for("dashboard.index"))

    code = request.args.get("code")
    if not code:
        flash("No authorization code received.", "error")
        return redirect(url_for("dashboard.index"))

    try:
        token_data = exchange_code_for_token(code)
        expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

        # Save token
        save_auth_token(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            expires_at=expires_at.isoformat(),
        )

        # Get user profile
        client = GraphClient()
        profile = client.get_user_profile()
        if profile:
            save_auth_token(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", ""),
                expires_at=expires_at.isoformat(),
                user_email=profile.get("mail", profile.get("userPrincipalName", "")),
                user_name=profile.get("displayName", ""),
            )

        flash("Connected to Office 365! Running first email sync...", "success")

        # Auto-sync emails immediately after connecting
        from task_tracker.routes.sync_routes import sync_emails
        result = sync_emails()
        if result.get("error"):
            flash(f"Sync issue: {result['error']}", "error")
        else:
            flash(f"Found {result['new_tasks']} tasks from {result['emails_checked']} emails.", "success")

    except Exception as e:
        flash(f"Authentication error: {str(e)}", "error")

    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout")
def logout():
    """Disconnect Office 365 and clear tokens."""
    clear_auth_token()
    session.clear()
    flash("Disconnected from Office 365.", "info")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/status")
def status():
    """Return authentication status as JSON."""
    from flask import jsonify
    token = get_auth_token()
    if token:
        return jsonify({
            "authenticated": True,
            "user_email": token.get("user_email", ""),
            "user_name": token.get("user_name", ""),
        })
    return jsonify({"authenticated": False})
