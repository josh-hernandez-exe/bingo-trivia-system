"""Dry-run transport — never hits the network. Used by `bts send --dry-run`."""

from __future__ import annotations

import logging
import uuid

from .base import Attachment, SendResult

logger = logging.getLogger(__name__)


class DryRunTransport:
    name = "dry-run"

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: list[Attachment],
        *,
        from_addr: str | None = None,
        bcc: list[str] | None = None,
    ) -> SendResult:
        att_sizes = [(a.filename, len(a.content)) for a in attachments]
        logger.info(
            "dry-run: would send subject=%r bcc=%s attachments=%s html_bytes=%d",
            subject,
            bcc or [],
            att_sizes,
            len(html),
        )
        return SendResult(to=to, ok=True, message_id=f"dryrun-{uuid.uuid4()}")
