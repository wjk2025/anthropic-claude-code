# Office 365 Email Task Tracker

A web application that connects to your Office 365 email, automatically detects actionable tasks from incoming messages, and provides a dashboard to track them through completion.

## Features

- **Office 365 Integration** — OAuth2 connection to Microsoft Graph API for reading emails
- **Smart Task Detection** — Keyword-based parsing identifies action items, deadlines, and assignments from email content
- **Task Dashboard** — View, filter, sort, and manage all your tasks in one place
- **Priority & Deadlines** — Automatic priority detection (Urgent/High/Medium/Low) and due date extraction
- **Status Workflow** — Track tasks through: New → In Progress → Waiting → Completed → Archived
- **Categories** — Auto-categorization: Review, Response, Deliverable, Meeting, Follow-up, General
- **Manual Tasks** — Create tasks manually alongside email-sourced tasks
- **Inline Editing** — Edit task details directly from the detail view

## Setup

### 1. Register an Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**
2. Name: `Task Tracker` (or anything you prefer)
3. Supported account types: **Single tenant** (your org only) or **Multitenant** for personal accounts
4. Redirect URI: `Web` → `http://localhost:5000/auth/callback`
5. After creating, note down:
   - **Application (client) ID** → `O365_CLIENT_ID`
   - **Directory (tenant) ID** → `O365_TENANT_ID`
6. Go to **Certificates & secrets** → **New client secret** → copy the value → `O365_CLIENT_SECRET`
7. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**:
   - `Mail.Read`
   - `Mail.ReadBasic`
   - `User.Read`

### 2. Configure Environment

```bash
cd task_tracker
cp .env.example .env
# Edit .env with your Azure AD credentials
```

### 3. Install Dependencies

```bash
pip install -r task_tracker/requirements.txt
```

### 4. Run

```bash
python -m task_tracker.run
```

Open **http://localhost:5000** in your browser. Click **Connect Office 365** to authenticate, then **Sync Emails** to scan your inbox.

## How Task Detection Works

The parser scans email subjects and bodies for patterns like:

| Pattern | Example |
|---------|---------|
| Direct requests | "Please review", "Can you update", "Need you to" |
| Assignments | "Assigned to you", "Your responsibility" |
| Deadlines | "Due by Friday", "Deadline: 3/15", "By EOD" |
| Urgency | "ASAP", "Urgent", "Time-sensitive" |
| Action items | "Action required", "Follow-up required" |

Priority is determined by keywords (`urgent`/`asap` → Urgent, `important` → High, `no rush` → Low) and the email's importance flag.

Due dates are extracted from absolute dates (`by 3/15/2026`) and relative references (`by end of week`, `within 3 days`).

## Architecture

```
task_tracker/
├── app.py                  # Flask application factory
├── config.py               # Configuration from environment
├── run.py                  # Entry point
├── graph_api/
│   ├── auth.py             # OAuth2 flow (login, token exchange, refresh)
│   └── client.py           # Microsoft Graph API client (email fetching)
├── parser/
│   └── email_parser.py     # Email → Task extraction engine
├── models/
│   └── database.py         # SQLite models, CRUD operations
├── routes/
│   ├── auth_routes.py      # /auth/login, /auth/callback, /auth/logout
│   ├── dashboard_routes.py # Dashboard views + JSON API
│   └── sync_routes.py      # Email sync trigger
├── templates/
│   ├── base.html           # Base layout with nav
│   ├── dashboard.html      # Main task list + stats + filters
│   └── task_detail.html    # Individual task view/edit
└── static/
    ├── css/style.css       # Full dashboard styling
    └── js/app.js           # AJAX updates, modals, toasts
```
