"""Dashboard routes for the task tracking web app."""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash

from task_tracker.models.database import (
    get_all_tasks,
    get_task,
    create_task,
    update_task,
    delete_task,
    get_task_stats,
    get_auth_token,
    Task,
    TaskStatus,
    TaskPriority,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Main dashboard view."""
    status_filter = request.args.get("status", "all")
    priority_filter = request.args.get("priority", "all")
    category_filter = request.args.get("category", "")
    search = request.args.get("search", "")

    tasks = get_all_tasks(
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        search=search,
    )
    stats = get_task_stats()
    auth = get_auth_token()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        stats=stats,
        auth=auth,
        filters={
            "status": status_filter,
            "priority": priority_filter,
            "category": category_filter,
            "search": search,
        },
        statuses=TaskStatus,
        priorities=TaskPriority,
    )


@dashboard_bp.route("/task/<int:task_id>")
def task_detail(task_id: int):
    """Task detail view."""
    task = get_task(task_id)
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("dashboard.index"))
    return render_template("task_detail.html", task=task, statuses=TaskStatus, priorities=TaskPriority)


@dashboard_bp.route("/task/create", methods=["POST"])
def create_manual_task():
    """Create a task manually (not from email)."""
    task = Task(
        title=request.form.get("title", ""),
        description=request.form.get("description", ""),
        priority=TaskPriority(request.form.get("priority", "medium")),
        category=request.form.get("category", "General"),
        due_date=request.form.get("due_date") or None,
    )
    create_task(task)
    flash("Task created.", "success")
    return redirect(url_for("dashboard.index"))


# --- API endpoints for AJAX ---

@dashboard_bp.route("/api/tasks")
def api_list_tasks():
    """JSON API to list tasks."""
    tasks = get_all_tasks(
        status=request.args.get("status"),
        priority=request.args.get("priority"),
        category=request.args.get("category"),
        search=request.args.get("search"),
    )
    return jsonify([t.to_dict() for t in tasks])


@dashboard_bp.route("/api/task/<int:task_id>", methods=["PATCH"])
def api_update_task(task_id: int):
    """Update a task field via AJAX."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    allowed_fields = {"status", "priority", "category", "title", "description", "due_date", "notes", "tags"}
    updates = {k: v for k, v in data.items() if k in allowed_fields}

    if not updates:
        return jsonify({"error": "No valid fields"}), 400

    task = update_task(task_id, updates)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task.to_dict())


@dashboard_bp.route("/api/task/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id: int):
    """Delete a task via AJAX."""
    if delete_task(task_id):
        return jsonify({"success": True})
    return jsonify({"error": "Task not found"}), 404


@dashboard_bp.route("/api/stats")
def api_stats():
    """Get dashboard statistics."""
    return jsonify(get_task_stats())
