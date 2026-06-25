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

        def send(self, to, subject, html, attachments, *, from_addr=None, bcc=None):
            sent.append(
                {
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "attachments": attachments,
                    "bcc": bcc,
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
        bcc=None,
        bcc_sender=None,
    )

    assert len(sent) == 1
    assert "attached as a fillable PDF" in sent[0]["html"]
    assert "Print the attached PDF" in sent[0]["html"]
    assert "Microsoft Edge or Adobe Acrobat" in sent[0]["html"]
    assert "tick the fillable checkboxes" in sent[0]["html"]
    attachments = sent[0]["attachments"]
    assert [attachment.filename for attachment in attachments] == [f"{card_id}.fillable.pdf"]
    assert attachments[0].content == b"fillable pdf"
    assert sent[0]["bcc"] == []


def test_send_uses_event_email_template_override(tmp_path, monkeypatch):
    event_root = tmp_path / "evt"
    pdf_dir = event_root / "cards" / "pdf"
    email_dir = event_root / "email"
    runs_dir = event_root / "runs"
    pdf_dir.mkdir(parents=True)
    email_dir.mkdir()
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
    (pdf_dir / f"{card_id}.fillable.pdf").write_bytes(b"fillable pdf")
    (email_dir / "invite.html.j2").write_text(
        "Custom invite for {{ display_name }} at {{ event.title }} with {{ card_id }}"
    )

    sent: list[dict[str, object]] = []

    class CaptureTransport:
        name = "capture"

        def send(self, to, subject, html, attachments, *, from_addr=None, bcc=None):
            sent.append({"to": to, "subject": subject, "html": html})
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
        bcc=None,
        bcc_sender=None,
    )

    assert sent[0]["html"] == f"Custom invite for A at Test Event with {card_id}"


def test_send_bcc_sender_from_event_config(tmp_path, monkeypatch):
    event_root = tmp_path / "evt"
    pdf_dir = event_root / "cards" / "pdf"
    email_dir = event_root / "email"
    runs_dir = event_root / "runs"
    pdf_dir.mkdir(parents=True)
    email_dir.mkdir()
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
    (email_dir / "send.yaml").write_text("bcc_sender: true\nbcc:\n  - audit@example.com\n")
    (pdf_dir / f"{card_id}.fillable.pdf").write_bytes(b"fillable pdf")

    sent: list[dict[str, object]] = []

    class CaptureTransport:
        name = "capture"

        def send(self, to, subject, html, attachments, *, from_addr=None, bcc=None):
            sent.append({"to": to, "bcc": bcc})
            return SendResult(to=to, ok=True, message_id="message-1")

    monkeypatch.setenv("SES_FROM_ADDR", "sender@example.com")
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
        bcc=None,
        bcc_sender=None,
    )

    assert sent == [
        {"to": "a@example.com", "bcc": ["audit@example.com", "sender@example.com"]}
    ]
    logs = sorted(runs_dir.glob("send-*.jsonl"))
    rows = [json.loads(line) for line in logs[-1].read_text().splitlines()]
    assert rows[0]["bcc"] == ["audit@example.com", "sender@example.com"]
