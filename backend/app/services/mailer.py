"""Sends email through Resend's HTTPS API (Railway often blocks SMTP), or SMTP if configured."""
import base64
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# attachments: (filename, content type, bytes)
Attachment = Tuple[str, str, bytes]


def configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY") or os.environ.get("SMTP_HOST"))


def send_mail(
    to: List[str],
    subject: str,
    text: str,
    attachments: Optional[List[Attachment]] = None,
    reply_to: Optional[str] = None,
) -> bool:
    sender = os.environ.get("MAIL_FROM", "OpportunityGenie <info@opportunitygenie.org>")
    attachments = attachments or []
    key = os.environ.get("RESEND_API_KEY")
    try:
        if key:
            body = {"from": sender, "to": to, "subject": subject, "text": text}
            if reply_to:
                body["reply_to"] = reply_to
            if attachments:
                body["attachments"] = [
                    {"filename": n, "content": base64.b64encode(d).decode("ascii")} for n, _t, d in attachments
                ]
            r = httpx.post(
                "https://api.resend.com/emails",
                json=body,
                headers={"Authorization": f"Bearer {key}"},
                timeout=30.0,
            )
            if r.status_code >= 300:
                logger.error("Resend rejected the email (%s): %s", r.status_code, r.text[:300])
                return False
            return True

        host = os.environ.get("SMTP_HOST")
        if host:
            msg = EmailMessage()
            msg["From"], msg["To"], msg["Subject"] = sender, ", ".join(to), subject
            if reply_to:
                msg["Reply-To"] = reply_to
            msg.set_content(text)
            for n, t, d in attachments:
                main, _, sub = t.partition("/")
                msg.add_attachment(d, maintype=main, subtype=sub or "octet-stream", filename=n)
            port = int(os.environ.get("SMTP_PORT", "587"))
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.starttls()
                user = os.environ.get("SMTP_USER")
                if user:
                    s.login(user, os.environ.get("SMTP_PASSWORD", ""))
                s.send_message(msg)
            return True
    except Exception:
        logger.exception("Sending email failed")
        return False
    logger.warning("No email provider configured (set RESEND_API_KEY)")
    return False
