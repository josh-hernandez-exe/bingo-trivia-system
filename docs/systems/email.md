# email

`src/bingo_trivia_system/email/`

Email transports (`graph`, `ses`, `dry-run`) + roster ↔ card assignment.

## Transports

All transports conform to `TransportProtocol`:

```python
class TransportProtocol(Protocol):
    name: str
    def send(self, to: str, subject: str, html: str,
             attachments: list[Attachment], *, from_addr: str | None = None) -> SendResult: ...
```

| Transport | Auth | Notes |
|---|---|---|
| `graph` | MSAL device-code (delegated) | Sends from your own mailbox. First call triggers an interactive login; token cached in `~/.cache/bts/`. Requires `uv sync --extra graph`. |
| `ses` | `boto3` (AWS profile) | Set `SES_FROM_ADDR`. Sender must be SES-verified. Requires `uv sync --extra ses`. |
| `dry-run` | none | Writes the send log but never hits the network. |

## Roster

`roster.csv` columns: `email,display_name`. `bts roster assign` maps each
email to one unused card (lowest UUID first → deterministic). Idempotent —
re-running preserves existing mappings. `bts roster reassign --email <x>`
swaps a participant to a different unused card.

## Resumable send

Every `bts send` run writes `events/<id>/runs/send-<ts>.jsonl`. The next run
inspects the latest log and skips anyone already marked `ok: true`. Pass
`--force` to bypass.

## Attachments

`bts cards render --mode both` writes print and fillable PDFs, but `bts send`
attaches only `<card-id>.fillable.pdf`. The fillable/checkmark PDF can be opened
in Adobe-compatible viewers and can still be printed by participants.

## Attachment size

Graph's "simple" `sendMail` caps at ~3 MB. The transport refuses an attachment
larger than 2.5 MB so failures surface before hitting the API.

## Privacy

Real `roster.csv` and `assignments.json` are **gitignored**. Only the
`events/example-*/` sample is committed and uses `@example.com` addresses.
