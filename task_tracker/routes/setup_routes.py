"""Setup wizard routes for first-time Azure AD configuration."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from task_tracker.models.database import save_app_settings, get_app_settings, is_setup_complete

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


@setup_bp.route("/")
def index():
    """Show the setup wizard."""
    settings = get_app_settings()
    return render_template("setup.html", settings=settings)


@setup_bp.route("/save", methods=["POST"])
def save():
    """Save Azure AD credentials from the setup form."""
    client_id = request.form.get("client_id", "").strip()
    client_secret = request.form.get("client_secret", "").strip()
    tenant_id = request.form.get("tenant_id", "").strip()
    redirect_uri = request.form.get("redirect_uri", "").strip()

    if not all([client_id, client_secret, tenant_id, redirect_uri]):
        flash("All fields are required.", "error")
        return redirect(url_for("setup.index"))

    save_app_settings(client_id, client_secret, tenant_id, redirect_uri)
    flash("Settings saved! Connecting to Microsoft...", "success")
    return redirect(url_for("auth.login"))
