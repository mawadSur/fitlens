"""Communication connectors: Email (SMTP) and Microsoft Teams (Graph)."""
from __future__ import annotations

from email.message import EmailMessage

import httpx

from ..config import settings
from .base import BaseConnector


class EmailConnector(BaseConnector):
    name = "email"
    category = "comms"
    required_env = ["smtp_host", "smtp_user", "smtp_password"]
    note = "Set SMTP_* (or MS Graph) to send real outreach/follow-ups."

    def send(self, to: str, subject: str, body: str) -> dict:
        if not self.is_live:
            return {"sent": False, "mode": "mock", "to": to, "subject": subject}
        msg = EmailMessage()  # pragma: no cover - requires SMTP server
        msg["From"] = settings.smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        import smtplib

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
            s.starttls()
            s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return {"sent": True, "mode": "live", "to": to, "subject": subject}


class TeamsConnector(BaseConnector):
    name = "teams"
    category = "comms"
    required_env = ["ms_graph_tenant_id", "ms_graph_client_id", "ms_graph_client_secret"]
    note = "🔴 Requires Azure app registration with Graph ChatMessage.Send."

    def send(self, to: str, subject: str, body: str) -> dict:
        if not self.is_live:
            return {"sent": False, "mode": "mock", "to": to, "subject": subject}
        # Live path: client-credentials token -> Graph chat message.  # pragma: no cover
        tenant = settings.ms_graph_tenant_id
        with httpx.Client(timeout=20) as c:
            tok = c.post(
                f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.ms_graph_client_id,
                    "client_secret": settings.ms_graph_client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            ).json()
            access_token = tok["access_token"]
            # `to` is the chat (conversation) id to post the message into.
            resp = c.post(
                f"https://graph.microsoft.com/v1.0/chats/{to}/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"body": {"contentType": "html", "content": f"<b>{subject}</b><br/>{body}"}},
            )
            resp.raise_for_status()
            return {"sent": True, "mode": "live", "to": to, "subject": subject, "id": resp.json().get("id")}


COMMS = [EmailConnector, TeamsConnector]
