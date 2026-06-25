import json
from importlib import import_module
from uuid import UUID

import yaml
from fastapi.testclient import TestClient

from bingo_trivia_system.config import EventPaths
from bingo_trivia_system.models import (
    FREE_CELL,
    Assignment,
    Assignments,
    Card,
    WordBank,
    WordBankEntry,
)
from bingo_trivia_system.webui.presenter import PresenterSession, reset_session

web_app = import_module("bingo_trivia_system.webui.app")


def test_expected_winners_returns_full_order(tmp_path, monkeypatch):
    event_id = "webui-winners"
    event_root = tmp_path / event_id
    cards_dir = event_root / "cards"
    cards_dir.mkdir(parents=True)

    entry_ids = [f"e{row}{col}" for row in range(5) for col in range(5) if (row, col) != (2, 2)]
    wordbank = WordBank(
        entries=[WordBankEntry(id=entry_id, text=entry_id, tier="easy") for entry_id in entry_ids]
    )
    grid = [
        ["e00", "e01", "e02", "e03", "e04"],
        ["e10", "e11", "e12", "e13", "e14"],
        ["e20", "e21", FREE_CELL, "e23", "e24"],
        ["e30", "e31", "e32", "e33", "e34"],
        ["e40", "e41", "e42", "e43", "e44"],
    ]

    (event_root / "event.yaml").write_text(
        yaml.safe_dump({"id": event_id, "title": "Web UI Winners", "win_rule": "corners"})
    )
    (event_root / "wordbank.yaml").write_text(yaml.safe_dump(wordbank.model_dump(mode="json")))
    (event_root / "questions.yaml").write_text(
        yaml.safe_dump(
            {
                "questions": [
                    {
                        "index": 1,
                        "prompt": "Mark the corners",
                        "answer_ids": ["e00", "e04", "e40", "e44"],
                    }
                ]
            }
        )
    )
    for index in range(26):
        card = Card(id=UUID(int=index + 1), event_id=event_id, grid=grid, seed=index)
        (cards_dir / f"{card.id}.json").write_text(json.dumps(card.model_dump(mode="json")))

    monkeypatch.setattr(
        web_app,
        "event_paths",
        lambda event: EventPaths(event_id=event_id, root=event_root),
    )
    reset_session(event_id)
    client = TestClient(web_app.create_app())

    client.post(f"/event/{event_id}/present/advance")
    response = client.get(f"/event/{event_id}/expected-winners")

    assert response.status_code == 200
    body = response.json()
    assert body["upto_question"] == 1
    assert len(body["winners"]) == 26
    assert [winner["won_at"] for winner in body["winners"]] == [1] * 26


def test_presenter_uses_answer_text_not_internal_ids(tmp_path, monkeypatch):
    event_id = "webui-presenter-answers"
    event_root = tmp_path / event_id
    (event_root / "cards").mkdir(parents=True)

    wordbank = WordBank(
        entries=[WordBankEntry(id="q01-answer-id", text="Human Answer", tier="easy")]
    )
    (event_root / "event.yaml").write_text(yaml.safe_dump({"id": event_id, "title": "Presenter"}))
    (event_root / "wordbank.yaml").write_text(yaml.safe_dump(wordbank.model_dump(mode="json")))
    (event_root / "questions.yaml").write_text(
        yaml.safe_dump(
            {"questions": [{"index": 1, "prompt": "Question?", "answer_ids": ["q01-answer-id"]}]}
        )
    )

    monkeypatch.setattr(
        web_app,
        "event_paths",
        lambda event: EventPaths(event_id=event_id, root=event_root),
    )
    reset_session(event_id)
    client = TestClient(web_app.create_app())

    response = client.get(f"/event/{event_id}/present")

    assert response.status_code == 200
    assert '"text": "Human Answer"' in response.text
    assert "1 · q01-answer-id" not in response.text


def test_presenter_serves_event_images(tmp_path, monkeypatch):
    event_id = "webui-presenter-images"
    event_root = tmp_path / event_id
    images_dir = event_root / "images" / "nested"
    images_dir.mkdir(parents=True)
    (images_dir / "photo.png").write_bytes(b"fake image bytes")
    (event_root / "cards").mkdir(parents=True)

    wordbank = WordBank(entries=[WordBankEntry(id="answer", text="Answer", tier="easy")])
    (event_root / "event.yaml").write_text(yaml.safe_dump({"id": event_id, "title": "Images"}))
    (event_root / "wordbank.yaml").write_text(yaml.safe_dump(wordbank.model_dump(mode="json")))
    (event_root / "questions.yaml").write_text(
        yaml.safe_dump(
            {
                "questions": [
                    {
                        "index": 1,
                        "prompt": "Question?",
                        "answer_ids": ["answer"],
                        "image": "nested/photo.png",
                    }
                ]
            }
        )
    )

    monkeypatch.setattr(
        web_app,
        "event_paths",
        lambda event: EventPaths(event_id=event_id, root=event_root),
    )
    reset_session(event_id)
    client = TestClient(web_app.create_app())

    presenter = client.get(f"/event/{event_id}/present")
    image = client.get(f"/event/{event_id}/images/nested/photo.png")
    traversal = client.get(f"/event/{event_id}/images/../event.yaml")

    assert presenter.status_code == 200
    assert "/event/${eventId}/images/" in presenter.text
    assert image.status_code == 200
    assert image.content == b"fake image bytes"
    assert traversal.status_code == 404


def test_search_finds_display_name(tmp_path, monkeypatch):
    event_id = "webui-search-name"
    event_root = tmp_path / event_id
    cards_dir = event_root / "cards"
    cards_dir.mkdir(parents=True)

    grid = [
        ["answer", "a", "b", "c", "d"],
        ["e", "f", "g", "h", "i"],
        ["j", "k", FREE_CELL, "l", "m"],
        ["n", "o", "p", "q", "r"],
        ["s", "t", "u", "v", "w"],
    ]
    entries = [
        WordBankEntry(id=cell, text=cell, tier="easy")
        for row in grid
        for cell in row
        if cell != FREE_CELL
    ]
    wordbank = WordBank(entries=entries)
    card = Card(id=UUID(int=1), event_id=event_id, grid=grid, seed=1)

    (event_root / "event.yaml").write_text(yaml.safe_dump({"id": event_id, "title": "Search"}))
    (event_root / "wordbank.yaml").write_text(yaml.safe_dump(wordbank.model_dump(mode="json")))
    (event_root / "questions.yaml").write_text(
        yaml.safe_dump(
            {"questions": [{"index": 1, "prompt": "Question?", "answer_ids": ["answer"]}]}
        )
    )
    (cards_dir / f"{card.id}.json").write_text(json.dumps(card.model_dump(mode="json")))
    assignments = Assignments(
        event_id=event_id,
        assignments=[
            Assignment(
                email="alex@example.com",
                card_id=card.id,
                display_name="Alex Searchable",
            )
        ],
    )
    (event_root / "assignments.json").write_text(json.dumps(assignments.model_dump(mode="json")))

    monkeypatch.setattr(
        web_app,
        "event_paths",
        lambda event: EventPaths(event_id=event_id, root=event_root),
    )
    reset_session(event_id)
    client = TestClient(web_app.create_app())

    response = client.get(f"/event/{event_id}/search?q=searchable")

    assert response.status_code == 200
    assert response.json() == [
        {
            "email": "alex@example.com",
            "card_id": str(card.id),
            "display_name": "Alex Searchable",
        }
    ]


def test_admin_expected_winners_has_separate_name_and_email_columns(tmp_path, monkeypatch):
    event_id = "webui-admin-columns"
    event_root = tmp_path / event_id
    (event_root / "cards").mkdir(parents=True)

    wordbank = WordBank(entries=[WordBankEntry(id="answer", text="Answer", tier="easy")])
    (event_root / "event.yaml").write_text(yaml.safe_dump({"id": event_id, "title": "Admin"}))
    (event_root / "wordbank.yaml").write_text(yaml.safe_dump(wordbank.model_dump(mode="json")))
    (event_root / "questions.yaml").write_text(
        yaml.safe_dump(
            {"questions": [{"index": 1, "prompt": "Question?", "answer_ids": ["answer"]}]}
        )
    )

    monkeypatch.setattr(
        web_app,
        "event_paths",
        lambda event: EventPaths(event_id=event_id, root=event_root),
    )
    reset_session(event_id)
    client = TestClient(web_app.create_app())

    response = client.get(f"/event/{event_id}")

    assert response.status_code == 200
    assert "<th>player name</th>" in response.text
    assert "<th>email</th>" in response.text
    assert "${w.display_name || ''}</td><td>${w.email || ''}" in response.text


def test_presenter_uses_in_page_verifier_and_local_timer(tmp_path, monkeypatch):
    event_id = "webui-presenter-controls"
    event_root = tmp_path / event_id
    (event_root / "cards").mkdir(parents=True)

    wordbank = WordBank(entries=[WordBankEntry(id="answer", text="Answer", tier="easy")])
    (event_root / "event.yaml").write_text(yaml.safe_dump({"id": event_id, "title": "Presenter"}))
    (event_root / "wordbank.yaml").write_text(yaml.safe_dump(wordbank.model_dump(mode="json")))
    (event_root / "questions.yaml").write_text(
        yaml.safe_dump(
            {"questions": [{"index": 1, "prompt": "Question?", "answer_ids": ["answer"]}]}
        )
    )

    monkeypatch.setattr(
        web_app,
        "event_paths",
        lambda event: EventPaths(event_id=event_id, root=event_root),
    )
    reset_session(event_id)
    client = TestClient(web_app.create_app())

    response = client.get(f"/event/{event_id}/present")

    assert response.status_code == 200
    assert "prompt(" not in response.text
    assert "verifyOverlay" in response.text
    assert "verifyResults" in response.text
    assert "Search by name, email, or card ID" in response.text
    assert "/search?q=" in response.text
    assert 'style="display:none;"' in response.text
    assert "function timerText" in response.text
    assert "setInterval(renderTimer, 1000)" in response.text
    assert "answerPassOverlay" in response.text
    assert "answer-pass" in response.text


def test_presenter_timer_pause_and_add_time_account_for_elapsed_time(tmp_path, monkeypatch):
    now = 1000.0
    monkeypatch.setattr("bingo_trivia_system.webui.presenter.time.time", lambda: now)
    session = PresenterSession("timer-event", tmp_path)

    session.advance()
    now = 1020.0
    session.pause()

    assert session.state.paused is True
    assert session.state.started_at is None
    assert session.state.timer_remaining == 40

    now = 1030.0
    session.pause()
    assert session.state.paused is False
    assert session.state.started_at == 1030.0
    assert session.state.timer_remaining == 40

    now = 1040.0
    session.add_time(30)

    assert session.state.started_at == 1040.0
    assert session.state.timer_remaining == 60


def test_presenter_answer_pass_toggle_persists_across_advance(tmp_path):
    session = PresenterSession("answer-pass-event", tmp_path)

    session.toggle_answer_pass()
    session.advance()
    session.advance()

    assert session.state.answer_pass is True
    assert session.state.revealed is False
