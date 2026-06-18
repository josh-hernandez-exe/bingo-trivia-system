import json

from bingo_trivia_system import cli
from bingo_trivia_system.config import EventPaths
from bingo_trivia_system.email.base import SendResult


def test_send_attaches_only_fillable_pdf(tmp_path, monkeypatch):
    event_root = tmp_path / "evt"
    pdf_dir = event_root / "cards" / "pdf"
    runs_dir = event_root / "runs"
    pdf_dir.mkdir(parents=True)
    runs_dir.mkdir()

    card_id = "00000000-0000-0000-0000-000000000001"
    (event_root / "event.yaml").write_text("id: evt\ntitle: Test Event\nnum_cards: 1\n")
    (event_root / "assignments.json").write_text(
        json.dumps(
            {
                "event_id": "evt",
                "assignments": [
                    {
                        "email": "a@example.com",
                        "display_name": "A",
                        "card_id": card_id,
                    }
                ],
            }
        )
    )
    (pdf_dir / f"{card_id}.print.pdf").write_bytes(b"print pdf")
    (pdf_dir / f"{card_id}.fillable.pdf").write_bytes(b"fillable pdf")

    sent: list[dict[str, object]] = []

    class CaptureTransport:
        name = "capture"

        def send(self, to, subject, html, attachments, *, from_addr=None):
            sent.append(
                {
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "attachments": attachments,
                }
            )
            return SendResult(to=to, ok=True, message_id="message-1")

    monkeypatch.setattr(
        cli,
        "event_paths",
        lambda event: EventPaths(event_id="evt", root=event_root),
    )
    monkeypatch.setattr(cli, "get_transport", lambda name: CaptureTransport())

    cli.send(
        event="evt",
        transport="capture",
        dry_run=False,
        only=None,
        force=False,
        subject="Test subject",
    )

    assert len(sent) == 1
    attachments = sent[0]["attachments"]
    assert [attachment.filename for attachment in attachments] == [f"{card_id}.fillable.pdf"]
    assert attachments[0].content == b"fillable pdf"
