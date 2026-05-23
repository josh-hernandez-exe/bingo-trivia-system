"""AWS SES email transport via boto3 `send_raw_email`."""

from __future__ import annotations

import os
from email.message import EmailMessage

from .base import Attachment, SendResult


class SESTransport:
    name = "ses"

    def __init__(self) -> None:
        try:
            import boto3
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("SES transport requires the 'ses' extra: uv sync --extra ses") from e
        self.client = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self.default_from = os.environ.get("SES_FROM_ADDR")

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: list[Attachment],
        *,
        from_addr: str | None = None,
    ) -> SendResult:
        sender = from_addr or self.default_from
        if not sender:
            return SendResult(to=to, ok=False, error="no from-address (set SES_FROM_ADDR)")
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to
        msg.set_content("This message contains an HTML part. View in an HTML-capable client.")
        msg.add_alternative(html, subtype="html")
        for a in attachments:
            maintype, _, subtype = a.content_type.partition("/")
            msg.add_attachment(
                a.content,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=a.filename,
            )
        try:
            resp = self.client.send_raw_email(
                Source=sender,
                Destinations=[to],
                RawMessage={"Data": msg.as_bytes()},
            )
        except Exception as e:
            return SendResult(to=to, ok=False, error=str(e))
        return SendResult(to=to, ok=True, message_id=resp.get("MessageId"))
