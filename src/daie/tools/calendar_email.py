"""
Calendar and Email Integration Tool.

Provides email sending/reading and calendar event management.
All integrations are optional and configured via environment variables.
"""

import logging
import os
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)


class EmailTool(Tool):
    """
    Email tool using SMTP/IMAP from Python stdlib.

    Configured via environment variables:
    - ``EMAIL_HOST``: SMTP server host
    - ``EMAIL_PORT``: SMTP server port (default: 587)
    - ``EMAIL_USER``: Email username/address
    - ``EMAIL_PASSWORD``: Email password or app password
    - ``IMAP_HOST``: IMAP server host (for reading emails)
    - ``IMAP_PORT``: IMAP server port (default: 993)

    Example:
        >>> tool = EmailTool()
        >>> result = await tool.execute({
        ...     "action": "send",
        ...     "to": "recipient@example.com",
        ...     "subject": "Hello",
        ...     "body": "Test email from DAIE agent"
        ... })
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="email",
            description="Send and read emails using SMTP/IMAP. Configured via EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD env vars.",
            category=ToolCategory.API,
            version="1.0.0",
            author="DAIE",
            capabilities=["send_email", "read_inbox", "search_emails"],
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Email action",
                    required=True,
                    choices=["send", "read_inbox", "search"],
                ),
                ToolParameter(
                    name="to",
                    type="string",
                    description="Recipient email address (for 'send')",
                    required=False,
                ),
                ToolParameter(
                    name="subject",
                    type="string",
                    description="Email subject (for 'send')",
                    required=False,
                ),
                ToolParameter(
                    name="body",
                    type="string",
                    description="Email body text (for 'send')",
                    required=False,
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query (for 'search' action)",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Number of emails to retrieve (default: 10)",
                    required=False,
                    default=10,
                ),
            ],
        )
        super().__init__(metadata)

    def _get_config(self) -> Dict[str, str]:
        return {
            "smtp_host": os.environ.get("EMAIL_HOST", ""),
            "smtp_port": int(os.environ.get("EMAIL_PORT", "587")),
            "user": os.environ.get("EMAIL_USER", ""),
            "password": os.environ.get("EMAIL_PASSWORD", ""),
            "imap_host": os.environ.get("IMAP_HOST", ""),
            "imap_port": int(os.environ.get("IMAP_PORT", "993")),
        }

    async def _execute(self, params: Dict[str, Any]) -> Any:
        import asyncio

        action = params["action"]
        config = self._get_config()

        if not config["user"] or not config["password"]:
            return {
                "success": False,
                "error": "Email not configured. Set EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD environment variables.",
            }

        if action == "send":
            return await asyncio.to_thread(self._send_email, params, config)
        elif action == "read_inbox":
            return await asyncio.to_thread(self._read_inbox, params, config)
        elif action == "search":
            return await asyncio.to_thread(self._search_emails, params, config)

        return {"success": False, "error": f"Unknown action: {action}"}

    def _send_email(self, params: Dict, config: Dict) -> Dict[str, Any]:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        to_addr = params.get("to")
        subject = params.get("subject", "(No Subject)")
        body = params.get("body", "")

        if not to_addr:
            return {"success": False, "error": "'to' is required for send action"}

        msg = MIMEMultipart()
        msg["From"] = config["user"]
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
                server.starttls()
                server.login(config["user"], config["password"])
                server.sendmail(config["user"], to_addr, msg.as_string())
            return {"success": True, "message": f"Email sent to {to_addr}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_inbox(self, params: Dict, config: Dict) -> Dict[str, Any]:
        import imaplib
        import email

        limit = params.get("limit", 10)
        imap_host = config.get("imap_host") or config["smtp_host"]

        try:
            mail = imaplib.IMAP4_SSL(imap_host, config["imap_port"])
            mail.login(config["user"], config["password"])
            mail.select("INBOX")

            _, msg_ids = mail.search(None, "ALL")
            ids = msg_ids[0].split()[-limit:]

            emails = []
            for msg_id in reversed(ids):
                _, data = mail.fetch(msg_id, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="replace")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="replace")

                emails.append({
                    "from": msg.get("From", ""),
                    "subject": msg.get("Subject", ""),
                    "date": msg.get("Date", ""),
                    "body": body[:500],
                })

            mail.logout()
            return {"success": True, "emails": emails, "count": len(emails)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search_emails(self, params: Dict, config: Dict) -> Dict[str, Any]:
        import imaplib
        import email

        query = params.get("query", "")
        limit = params.get("limit", 10)
        imap_host = config.get("imap_host") or config["smtp_host"]

        try:
            mail = imaplib.IMAP4_SSL(imap_host, config["imap_port"])
            mail.login(config["user"], config["password"])
            mail.select("INBOX")

            _, msg_ids = mail.search(None, f'(SUBJECT "{query}")')
            ids = msg_ids[0].split()[-limit:]

            emails = []
            for msg_id in reversed(ids):
                _, data = mail.fetch(msg_id, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                emails.append({
                    "from": msg.get("From", ""),
                    "subject": msg.get("Subject", ""),
                    "date": msg.get("Date", ""),
                })

            mail.logout()
            return {"success": True, "emails": emails, "count": len(emails)}

        except Exception as e:
            return {"success": False, "error": str(e)}


class CalendarTool(Tool):
    """
    Calendar event management tool.

    Generates ICS calendar events. Optionally integrates with
    Google Calendar when ``google-api-python-client`` is installed
    and credentials are configured.

    Example:
        >>> tool = CalendarTool()
        >>> result = await tool.execute({
        ...     "action": "create_event",
        ...     "title": "Team Meeting",
        ...     "start": "2024-01-15T10:00:00",
        ...     "end": "2024-01-15T11:00:00",
        ... })
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="calendar",
            description="Create, list, and manage calendar events. Generates ICS files or integrates with Google Calendar.",
            category=ToolCategory.API,
            version="1.0.0",
            author="DAIE",
            capabilities=["create_event", "list_events", "generate_ics"],
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Calendar action",
                    required=True,
                    choices=["create_event", "list_events", "generate_ics"],
                ),
                ToolParameter(
                    name="title",
                    type="string",
                    description="Event title",
                    required=False,
                ),
                ToolParameter(
                    name="start",
                    type="string",
                    description="Event start time (ISO 8601 format, e.g., '2024-01-15T10:00:00')",
                    required=False,
                ),
                ToolParameter(
                    name="end",
                    type="string",
                    description="Event end time (ISO 8601 format)",
                    required=False,
                ),
                ToolParameter(
                    name="description",
                    type="string",
                    description="Event description",
                    required=False,
                ),
                ToolParameter(
                    name="location",
                    type="string",
                    description="Event location",
                    required=False,
                ),
                ToolParameter(
                    name="output_path",
                    type="string",
                    description="Path to save ICS file (for 'generate_ics')",
                    required=False,
                    default="event.ics",
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Any:
        import asyncio

        action = params["action"]

        if action == "create_event":
            return await asyncio.to_thread(self._create_ics_event, params)
        elif action == "generate_ics":
            return await asyncio.to_thread(self._create_ics_event, params)
        elif action == "list_events":
            return {"success": True, "events": [], "message": "Local event listing not yet supported. Use generate_ics to create events."}

        return {"success": False, "error": f"Unknown action: {action}"}

    def _create_ics_event(self, params: Dict) -> Dict[str, Any]:
        from datetime import datetime

        title = params.get("title", "Untitled Event")
        start = params.get("start")
        end = params.get("end")
        description = params.get("description", "")
        location = params.get("location", "")
        output_path = params.get("output_path", "event.ics")

        if not start:
            return {"success": False, "error": "'start' time is required"}

        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end) if end else start_dt
        except ValueError as e:
            return {"success": False, "error": f"Invalid datetime format: {e}"}

        # Generate ICS content (RFC 5545)
        import uuid

        uid = str(uuid.uuid4())
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//DAIE//Calendar Tool//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
DTSTART:{start_dt.strftime("%Y%m%dT%H%M%S")}
DTEND:{end_dt.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{title}
DESCRIPTION:{description}
LOCATION:{location}
END:VEVENT
END:VCALENDAR"""

        try:
            with open(output_path, "w") as f:
                f.write(ics)
            return {
                "success": True,
                "message": f"Event '{title}' created",
                "ics_path": output_path,
                "event": {
                    "title": title,
                    "start": start,
                    "end": end,
                    "description": description,
                    "location": location,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
