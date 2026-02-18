#!/usr/bin/env python3
"""Entry point to run the O365 Task Tracker web app."""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from task_tracker.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
