"""Email transport protocol + registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Attachment:
    filename: str
    content: bytes
    content_type: str = "application/pdf"


@dataclass
class SendResult:
    to: str
    ok: bool
    message_id: str | None = None
    error: str | None = None


class TransportProtocol(Protocol):
    """Pluggable email backend."""

    name: str

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: list[Attachment],
        *,
        from_addr: str | None = None,
    ) -> SendResult: ...


def get_transport(name: str) -> TransportProtocol:
    name = name.lower()
    if name == "graph":
        from .graph import GraphTransport

        return GraphTransport()
    if name == "ses":
        from .ses import SESTransport

        return SESTransport()
    if name == "dry-run":
        from .dryrun import DryRunTransport

        return DryRunTransport()
    raise ValueError(f"unknown transport {name!r}; expected 'graph', 'ses', or 'dry-run'")
