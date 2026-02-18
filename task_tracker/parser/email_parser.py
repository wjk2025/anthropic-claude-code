"""Email parser that extracts tasks from Office 365 emails."""

import re
from datetime import datetime, timedelta
from typing import Optional
from html import unescape

from task_tracker.models.database import Task, TaskPriority


# Keywords and patterns that indicate a task or action item
TASK_KEYWORDS = [
    r"\baction required\b",
    r"\baction items?\b",
    r"\bplease complete\b",
    r"\bplease review\b",
    r"\bplease update\b",
    r"\bplease send\b",
    r"\bplease provide\b",
    r"\bplease prepare\b",
    r"\bplease confirm\b",
    r"\bplease submit\b",
    r"\bplease follow[- ]up\b",
    r"\bassigned to you\b",
    r"\byour responsibility\b",
    r"\byou are responsible\b",
    r"\bcan you\b.*\?",
    r"\bcould you\b.*\?",
    r"\bwould you\b.*\?",
    r"\bneed you to\b",
    r"\bneed your\b",
    r"\bdeadline\b",
    r"\bdue by\b",
    r"\bdue date\b",
    r"\bby end of day\b",
    r"\bby eod\b",
    r"\bby cob\b",
    r"\basap\b",
    r"\burgent\b",
    r"\btime[- ]sensitive\b",
    r"\bhigh priority\b",
    r"\btodo\b",
    r"\bto[- ]do\b",
    r"\bfollow[- ]up required\b",
    r"\bwaiting on you\b",
    r"\bpending your\b",
    r"\bapproval needed\b",
    r"\bsign[- ]off needed\b",
    r"\binput needed\b",
    r"\bfeedback needed\b",
    r"\bresponse needed\b",
    r"\bresponse required\b",
]

# Patterns for extracting due dates from text
DATE_PATTERNS = [
    (r"\bby\s+(\d{1,2}/\d{1,2}/\d{2,4})\b", "%m/%d/%Y"),
    (r"\bby\s+(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
    (r"\bdue\s+(\d{1,2}/\d{1,2}/\d{2,4})\b", "%m/%d/%Y"),
    (r"\bdeadline:?\s*(\d{1,2}/\d{1,2}/\d{2,4})\b", "%m/%d/%Y"),
    (r"\bdeadline:?\s*(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
]

RELATIVE_DATE_PATTERNS = [
    (r"\bby\s+(?:end\s+of\s+)?today\b", 0),
    (r"\bby\s+(?:end\s+of\s+)?tomorrow\b", 1),
    (r"\beod\s+today\b", 0),
    (r"\beod\s+tomorrow\b", 1),
    (r"\bby\s+end\s+of\s+(?:this\s+)?week\b", None),  # special: next Friday
    (r"\bnext\s+week\b", 7),
    (r"\bwithin\s+(\d+)\s+days?\b", None),  # special: extract N
]

# Priority keyword mapping
PRIORITY_SIGNALS = {
    TaskPriority.URGENT: [r"\burgent\b", r"\basap\b", r"\bimmediately\b", r"\bcritical\b", r"\bemergency\b"],
    TaskPriority.HIGH: [r"\bhigh\s*priority\b", r"\bimportant\b", r"\btime[- ]sensitive\b", r"\bescalat"],
    TaskPriority.LOW: [r"\blow\s*priority\b", r"\bwhen\s+you\s+get\s+a\s+chance\b", r"\bno\s+rush\b", r"\bfyi\b"],
}

# Category detection patterns
CATEGORY_PATTERNS = {
    "Review": [r"\breview\b", r"\bfeedback\b", r"\bapproval\b", r"\bsign[- ]off\b"],
    "Response": [r"\breply\b", r"\brespond\b", r"\bresponse\b", r"\bconfirm\b", r"\banswer\b"],
    "Deliverable": [r"\bdeliver\b", r"\bsubmit\b", r"\bsend\b", r"\bprovide\b", r"\bprepare\b", r"\bcreate\b"],
    "Meeting": [r"\bmeeting\b", r"\bcall\b", r"\bschedule\b", r"\bappointment\b"],
    "Follow-up": [r"\bfollow[- ]up\b", r"\bcheck[- ]in\b", r"\bstatus update\b"],
}


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class EmailTaskParser:
    """Parses emails to detect and extract actionable tasks."""

    def __init__(self, user_email: str = ""):
        self.user_email = user_email.lower()

    def is_task_email(self, email: dict) -> bool:
        """Determine if an email contains a task for the user."""
        subject = email.get("subject", "")
        body_preview = email.get("bodyPreview", "")
        body_content = ""
        if email.get("body"):
            body_content = _strip_html(email["body"].get("content", ""))

        combined_text = f"{subject} {body_preview} {body_content}".lower()

        # Check if any task keyword matches
        for pattern in TASK_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return True

        # Check if email is flagged as high importance
        if email.get("importance") == "high":
            return True

        return False

    def extract_task(self, email: dict) -> Task:
        """Extract a Task object from an email."""
        subject = email.get("subject", "(No subject)")
        body_preview = email.get("bodyPreview", "")
        body_content = ""
        if email.get("body"):
            body_content = _strip_html(email["body"].get("content", ""))

        combined_text = f"{subject} {body_preview} {body_content}"

        sender = email.get("from", {}).get("emailAddress", {})
        sender_name = sender.get("name", "Unknown")
        sender_email = sender.get("address", "")

        received_at = email.get("receivedDateTime", "")

        title = self._extract_title(subject, combined_text)
        priority = self._detect_priority(combined_text, email.get("importance", "normal"))
        due_date = self._extract_due_date(combined_text)
        category = self._detect_category(combined_text)
        tags = self._extract_tags(email)
        description = self._build_description(body_preview, sender_name)

        return Task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            tags=tags,
            sender_name=sender_name,
            sender_email=sender_email,
            email_subject=subject,
            email_id=email.get("id", ""),
            email_received_at=received_at,
            due_date=due_date,
        )

    def _extract_title(self, subject: str, body: str) -> str:
        """Generate a concise task title from the email."""
        # Remove common prefixes
        title = re.sub(r"^(RE:|FW:|FWD:)\s*", "", subject, flags=re.IGNORECASE).strip()

        # If subject is generic, try to extract from body
        if not title or title.lower() in ("(no subject)", "action required", "urgent"):
            # Look for first action-like sentence
            sentences = re.split(r"[.!?\n]", body)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and any(
                    re.search(p, sentence, re.IGNORECASE) for p in TASK_KEYWORDS[:15]
                ):
                    title = sentence[:120]
                    break

        if not title:
            title = subject

        # Truncate if too long
        if len(title) > 120:
            title = title[:117] + "..."

        return title

    def _detect_priority(self, text: str, importance: str) -> TaskPriority:
        """Determine the priority level of the task."""
        text_lower = text.lower()

        # Check urgent first
        for pattern in PRIORITY_SIGNALS[TaskPriority.URGENT]:
            if re.search(pattern, text_lower):
                return TaskPriority.URGENT

        # High importance flag from email
        if importance == "high":
            return TaskPriority.HIGH

        for pattern in PRIORITY_SIGNALS[TaskPriority.HIGH]:
            if re.search(pattern, text_lower):
                return TaskPriority.HIGH

        for pattern in PRIORITY_SIGNALS[TaskPriority.LOW]:
            if re.search(pattern, text_lower):
                return TaskPriority.LOW

        return TaskPriority.MEDIUM

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Try to find a due date in the email text."""
        text_lower = text.lower()

        # Try absolute date patterns
        for pattern, fmt in DATE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    date_str = match.group(1)
                    # Handle 2-digit years
                    if fmt.endswith("%Y") and len(date_str.split("/")[-1]) == 2:
                        fmt = fmt.replace("%Y", "%y")
                    dt = datetime.strptime(date_str, fmt)
                    if dt.year < 100:
                        dt = dt.replace(year=dt.year + 2000)
                    return dt.date().isoformat()
                except ValueError:
                    continue

        # Try relative date patterns
        for pattern, days_offset in RELATIVE_DATE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                if days_offset is not None:
                    due = datetime.utcnow().date() + timedelta(days=days_offset)
                    return due.isoformat()
                elif "week" in pattern:
                    today = datetime.utcnow().date()
                    days_until_friday = (4 - today.weekday()) % 7
                    if days_until_friday == 0:
                        days_until_friday = 7
                    due = today + timedelta(days=days_until_friday)
                    return due.isoformat()

        # "within N days"
        match = re.search(r"\bwithin\s+(\d+)\s+days?\b", text_lower)
        if match:
            n = int(match.group(1))
            due = datetime.utcnow().date() + timedelta(days=n)
            return due.isoformat()

        return None

    def _detect_category(self, text: str) -> str:
        """Categorize the task based on content."""
        text_lower = text.lower()
        for category, patterns in CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return category
        return "General"

    def _extract_tags(self, email: dict) -> list[str]:
        """Extract relevant tags from the email metadata."""
        tags = []

        if email.get("importance") == "high":
            tags.append("high-importance")

        if email.get("hasAttachments"):
            tags.append("has-attachments")

        # Check if user is in CC (might be informational)
        cc_recipients = email.get("ccRecipients", [])
        if self.user_email and any(
            r.get("emailAddress", {}).get("address", "").lower() == self.user_email
            for r in cc_recipients
        ):
            tags.append("cc-recipient")

        subject = email.get("subject", "").lower()
        if subject.startswith("re:"):
            tags.append("reply-thread")
        if subject.startswith("fw:") or subject.startswith("fwd:"):
            tags.append("forwarded")

        return tags

    def _build_description(self, body_preview: str, sender_name: str) -> str:
        """Build a task description from the email content."""
        preview = body_preview.strip()
        if len(preview) > 300:
            preview = preview[:297] + "..."
        return f"From {sender_name}: {preview}"
