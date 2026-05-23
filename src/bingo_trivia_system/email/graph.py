"""Microsoft Graph email transport (delegated device-code auth).

Reads `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID` from the environment. The first
call triggers an interactive device-code login; the token is cached in
`~/.cache/bts/graph-token.json`.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path

import httpx

from .base import Attachment, SendResult

logger = logging.getLogger(__name__)
GRAPH_API = "https://graph.microsoft.com/v1.0"
TOKEN_CACHE = Path.home() / ".cache" / "bts" / "graph-token.json"
SCOPES = ["Mail.Send", "User.Read"]
MAX_SIMPLE_ATTACHMENT = int(2.5 * 1024 * 1024)


class GraphTransport:
    name = "graph"

    def __init__(self) -> None:
        try:
            import msal  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "Graph transport requires the 'graph' extra: uv sync --extra graph"
            ) from e
        self.tenant = os.environ["GRAPH_TENANT_ID"]
        self.client_id = os.environ["GRAPH_CLIENT_ID"]
        self._token: str | None = None

    def _acquire_token(self) -> str:
        if self._token:
            return self._token
        import msal

        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        cache = msal.SerializableTokenCache()
        if TOKEN_CACHE.exists():
            cache.deserialize(TOKEN_CACHE.read_text())
        app = msal.PublicClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant}",
            token_cache=cache,
        )
        accounts = app.get_accounts()
        result = None
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if not result:
            flow = app.initiate_device_flow(scopes=SCOPES)
            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
        if cache.has_state_changed:
            TOKEN_CACHE.write_text(cache.serialize())
        self._token = result["access_token"]
        return self._token

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: list[Attachment],
        *,
        from_addr: str | None = None,
    ) -> SendResult:
        for a in attachments:
            if len(a.content) > MAX_SIMPLE_ATTACHMENT:
                return SendResult(
                    to=to,
                    ok=False,
                    error=f"attachment {a.filename} exceeds 2.5 MB Graph simple-send limit",
                )
        token = self._acquire_token()
        body = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html},
                "toRecipients": [{"emailAddress": {"address": to}}],
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": a.filename,
                        "contentType": a.content_type,
                        "contentBytes": base64.b64encode(a.content).decode("ascii"),
                    }
                    for a in attachments
                ],
            },
            "saveToSentItems": True,
        }
        resp = httpx.post(
            f"{GRAPH_API}/me/sendMail",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            content=json.dumps(body),
            timeout=30,
        )
        if resp.status_code in (200, 202):
            return SendResult(to=to, ok=True, message_id=resp.headers.get("request-id"))
        return SendResult(to=to, ok=False, error=f"{resp.status_code}: {resp.text[:300]}")
