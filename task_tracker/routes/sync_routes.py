"""Email sync routes — trigger and manage email-to-task synchronization."""

from datetime import datetime
from flask import Blueprint, jsonify, flash, redirect, url_for

from task_tracker.graph_api.client import GraphClient
from task_tracker.parser.email_parser import EmailTaskParser
from task_tracker.models.database import (
    create_task,
    task_exists_for_email,
    get_auth_token,
    get_sync_state,
    update_sync_state,
)
from task_tracker.config import Config

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")


def sync_emails() -> dict:
    """Fetch new emails and create tasks for any that contain action items.

    Returns a summary dict with counts.
    """
    auth = get_auth_token()
    if not auth:
        return {"error": "Not authenticated", "new_tasks": 0, "emails_checked": 0}

    client = GraphClient()
    if not client.is_authenticated():
        return {"error": "Authentication expired", "new_tasks": 0, "emails_checked": 0}

    parser = EmailTaskParser(user_email=auth.get("user_email", ""))

    # Determine the time window
    sync_state = get_sync_state()
    since = sync_state["last_email_timestamp"] if sync_state else None

    emails = client.get_recent_emails(
        since=since,
        max_results=Config.MAX_EMAILS_PER_POLL,
    )

    new_tasks = 0
    latest_timestamp = since

    for email in emails:
        email_id = email.get("id", "")
        received = email.get("receivedDateTime", "")

        # Track the latest timestamp we've seen
        if not latest_timestamp or received > latest_timestamp:
            latest_timestamp = received

        # Skip if we already created a task for this email
        if task_exists_for_email(email_id):
            continue

        # Check if the email contains a task
        if parser.is_task_email(email):
            task = parser.extract_task(email)
            create_task(task)
            new_tasks += 1

    # Update sync state
    update_sync_state(
        last_sync_at=datetime.utcnow().isoformat(),
        last_email_timestamp=latest_timestamp,
    )

    return {
        "new_tasks": new_tasks,
        "emails_checked": len(emails),
        "last_sync": datetime.utcnow().isoformat(),
    }


@sync_bp.route("/now", methods=["POST"])
def sync_now():
    """Trigger an immediate email sync."""
    result = sync_emails()
    if result.get("error"):
        flash(f"Sync failed: {result['error']}", "error")
    else:
        flash(f"Sync complete: {result['new_tasks']} new tasks from {result['emails_checked']} emails.", "success")
    return redirect(url_for("dashboard.index"))


@sync_bp.route("/status")
def sync_status():
    """Get sync status as JSON."""
    state = get_sync_state()
    auth = get_auth_token()
    return jsonify({
        "authenticated": auth is not None,
        "last_sync": state["last_sync_at"] if state else None,
        "last_email_timestamp": state["last_email_timestamp"] if state else None,
    })
