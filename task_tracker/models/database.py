"""SQLite database models and operations for task tracking."""

import sqlite3
import json
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field, asdict


class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.MEDIUM
    category: str = ""
    tags: list[str] = field(default_factory=list)
    sender_name: str = ""
    sender_email: str = ""
    email_subject: str = ""
    email_id: str = ""
    email_received_at: Optional[str] = None
    due_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tags"] = json.dumps(d["tags"])
        return d

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Task":
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        d["status"] = TaskStatus(d["status"])
        d["priority"] = TaskPriority(d["priority"])
        return cls(**d)


_db_path: str = "task_tracker.db"


def init_db(db_path: str = "task_tracker.db") -> None:
    """Initialize the database and create tables."""
    global _db_path
    _db_path = db_path
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'new',
            priority TEXT NOT NULL DEFAULT 'medium',
            category TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            sender_name TEXT DEFAULT '',
            sender_email TEXT DEFAULT '',
            email_subject TEXT DEFAULT '',
            email_id TEXT DEFAULT '',
            email_received_at TEXT,
            due_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            notes TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expires_at TEXT NOT NULL,
            user_email TEXT DEFAULT '',
            user_name TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_sync_at TEXT,
            last_email_timestamp TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            client_id TEXT DEFAULT '',
            client_secret TEXT DEFAULT '',
            tenant_id TEXT DEFAULT '',
            redirect_uri TEXT DEFAULT '',
            setup_complete INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_email_id ON tasks(email_id)")
    conn.commit()
    conn.close()


def get_db() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(conn: sqlite3.Connection) -> None:
    """Close a database connection."""
    conn.close()


# --- Task CRUD operations ---

def create_task(task: Task) -> Task:
    """Insert a new task and return it with its ID."""
    now = datetime.utcnow().isoformat()
    task.created_at = now
    task.updated_at = now
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO tasks
               (title, description, status, priority, category, tags,
                sender_name, sender_email, email_subject, email_id,
                email_received_at, due_date, created_at, updated_at, completed_at, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.title, task.description, task.status.value, task.priority.value,
                task.category, json.dumps(task.tags),
                task.sender_name, task.sender_email, task.email_subject, task.email_id,
                task.email_received_at, task.due_date,
                task.created_at, task.updated_at, task.completed_at, task.notes,
            ),
        )
        conn.commit()
        task.id = cur.lastrowid
        return task
    finally:
        close_db(conn)


def get_task(task_id: int) -> Optional[Task]:
    """Get a single task by ID."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return Task.from_row(row) if row else None
    finally:
        close_db(conn)


def get_all_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Task]:
    """Get tasks with optional filters."""
    conn = get_db()
    try:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list = []

        if status and status != "all":
            query += " AND status = ?"
            params.append(status)

        if priority and priority != "all":
            query += " AND priority = ?"
            params.append(priority)

        if category:
            query += " AND category = ?"
            params.append(category)

        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR sender_name LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])

        query += " ORDER BY CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [Task.from_row(r) for r in rows]
    finally:
        close_db(conn)


def update_task(task_id: int, updates: dict) -> Optional[Task]:
    """Update specific fields on a task."""
    conn = get_db()
    try:
        updates["updated_at"] = datetime.utcnow().isoformat()
        if updates.get("status") == TaskStatus.COMPLETED.value:
            updates["completed_at"] = datetime.utcnow().isoformat()
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"])

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return get_task(task_id)
    finally:
        close_db(conn)


def delete_task(task_id: int) -> bool:
    """Delete a task by ID."""
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        close_db(conn)


def task_exists_for_email(email_id: str) -> bool:
    """Check if a task already exists for a given email ID."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM tasks WHERE email_id = ?", (email_id,)
        ).fetchone()
        return row is not None
    finally:
        close_db(conn)


def get_task_stats() -> dict:
    """Get dashboard statistics."""
    conn = get_db()
    try:
        stats = {}
        for status in TaskStatus:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE status = ?", (status.value,)
            ).fetchone()
            stats[status.value] = row["cnt"]

        stats["total"] = sum(stats.values())

        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE priority = 'urgent' AND status NOT IN ('completed', 'archived')"
        ).fetchone()
        stats["urgent_active"] = row["cnt"]

        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE due_date IS NOT NULL AND due_date < ? AND status NOT IN ('completed', 'archived')",
            (datetime.utcnow().isoformat(),),
        ).fetchone()
        stats["overdue"] = row["cnt"]

        return stats
    finally:
        close_db(conn)


# --- Auth token storage ---

def save_auth_token(access_token: str, refresh_token: str, expires_at: str,
                    user_email: str = "", user_name: str = "") -> None:
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO auth_tokens (id, access_token, refresh_token, expires_at, user_email, user_name)
               VALUES (1, ?, ?, ?, ?, ?)""",
            (access_token, refresh_token, expires_at, user_email, user_name),
        )
        conn.commit()
    finally:
        close_db(conn)


def get_auth_token() -> Optional[dict]:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM auth_tokens WHERE id = 1").fetchone()
        return dict(row) if row else None
    finally:
        close_db(conn)


def clear_auth_token() -> None:
    conn = get_db()
    try:
        conn.execute("DELETE FROM auth_tokens WHERE id = 1")
        conn.commit()
    finally:
        close_db(conn)


# --- Sync state ---

def get_sync_state() -> Optional[dict]:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM sync_state WHERE id = 1").fetchone()
        return dict(row) if row else None
    finally:
        close_db(conn)


def update_sync_state(last_sync_at: str, last_email_timestamp: Optional[str] = None) -> None:
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO sync_state (id, last_sync_at, last_email_timestamp)
               VALUES (1, ?, ?)""",
            (last_sync_at, last_email_timestamp),
        )
        conn.commit()
    finally:
        close_db(conn)


# --- App settings (Azure AD credentials) ---

def get_app_settings() -> Optional[dict]:
    """Get stored Azure AD app credentials."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
        return dict(row) if row else None
    finally:
        close_db(conn)


def save_app_settings(client_id: str, client_secret: str, tenant_id: str,
                      redirect_uri: str) -> None:
    """Save Azure AD app credentials to the database."""
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO app_settings
               (id, client_id, client_secret, tenant_id, redirect_uri, setup_complete)
               VALUES (1, ?, ?, ?, ?, 1)""",
            (client_id, client_secret, tenant_id, redirect_uri),
        )
        conn.commit()
    finally:
        close_db(conn)


def is_setup_complete() -> bool:
    """Check if initial Azure AD setup has been done."""
    settings = get_app_settings()
    return settings is not None and settings.get("setup_complete") == 1
