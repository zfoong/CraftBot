# -*- coding: utf-8 -*-
"""Outlook email client — IMAP/SMTP via standard library."""

from __future__ import annotations

import email
import email.mime.multipart
import email.mime.text
import imaplib
import logging
import smtplib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.external_comms.base import BasePlatformClient
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

CREDENTIAL_FILE = "outlook.json"

try:
    from app.logger import logger
except Exception:
    logger = logging.getLogger(__name__)


@dataclass
class OutlookCredential:
    email_address: str = ""
    password: str = ""  # App password for accounts with 2FA
    imap_server: str = "outlook.office365.com"
    smtp_server: str = "smtp.office365.com"
    imap_port: int = 993
    smtp_port: int = 587


@register_client
class OutlookClient(BasePlatformClient):
    PLATFORM_ID = "outlook"

    def __init__(self):
        super().__init__()
        self._cred: Optional[OutlookCredential] = None

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> OutlookCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, OutlookCredential)
        if self._cred is None:
            raise RuntimeError("No Outlook credentials. Use /outlook login first.")
        return self._cred

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        subject = kwargs.get("subject", "")
        return self.send_email(recipient, subject, text)

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def send_email(self, to: str, subject: str, body: str, cc: Optional[str] = None,
                   html: bool = False) -> Dict[str, Any]:
        cred = self._load()
        try:
            msg = email.mime.multipart.MIMEMultipart("alternative")
            msg["From"] = cred.email_address
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = cc

            content_type = "html" if html else "plain"
            msg.attach(email.mime.text.MIMEText(body, content_type, "utf-8"))

            with smtplib.SMTP(cred.smtp_server, cred.smtp_port) as server:
                server.starttls()
                server.login(cred.email_address, cred.password)
                recipients = [to]
                if cc:
                    recipients.extend([addr.strip() for addr in cc.split(",")])
                server.sendmail(cred.email_address, recipients, msg.as_string())

            return {"ok": True, "result": {"sent": True, "to": to, "subject": subject}}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_emails(self, folder: str = "INBOX", n: int = 10, unread_only: bool = False) -> Dict[str, Any]:
        cred = self._load()
        try:
            with imaplib.IMAP4_SSL(cred.imap_server, cred.imap_port) as imap:
                imap.login(cred.email_address, cred.password)
                imap.select(folder, readonly=True)

                criteria = "UNSEEN" if unread_only else "ALL"
                _, msg_ids = imap.search(None, criteria)
                ids = msg_ids[0].split()
                ids = ids[-n:] if len(ids) > n else ids
                ids.reverse()

                emails = []
                for mid in ids:
                    _, data = imap.fetch(mid, "(RFC822.HEADER)")
                    if data[0] is None:
                        continue
                    msg = email.message_from_bytes(data[0][1])
                    emails.append({
                        "id": mid.decode(),
                        "from": msg.get("From", ""),
                        "to": msg.get("To", ""),
                        "subject": msg.get("Subject", ""),
                        "date": msg.get("Date", ""),
                    })

            return {"ok": True, "result": {"emails": emails, "count": len(emails)}}
        except Exception as e:
            return {"error": str(e)}

    def get_email(self, message_id: str, folder: str = "INBOX") -> Dict[str, Any]:
        cred = self._load()
        try:
            with imaplib.IMAP4_SSL(cred.imap_server, cred.imap_port) as imap:
                imap.login(cred.email_address, cred.password)
                imap.select(folder, readonly=True)

                _, data = imap.fetch(message_id.encode(), "(RFC822)")
                if data[0] is None:
                    return {"error": f"Message {message_id} not found"}

                msg = email.message_from_bytes(data[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                            break
                        elif ct == "text/html" and not body:
                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

            return {"ok": True, "result": {
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body": body,
            }}
        except Exception as e:
            return {"error": str(e)}

    def list_folders(self) -> Dict[str, Any]:
        cred = self._load()
        try:
            with imaplib.IMAP4_SSL(cred.imap_server, cred.imap_port) as imap:
                imap.login(cred.email_address, cred.password)
                _, folders = imap.list()
                folder_names = []
                for f in folders:
                    if f:
                        name = f.decode().split('"/"')[-1].strip().strip('"')
                        folder_names.append(name)
            return {"ok": True, "result": {"folders": folder_names}}
        except Exception as e:
            return {"error": str(e)}
