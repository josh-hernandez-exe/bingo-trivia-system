import json
from importlib import import_module
from uuid import UUID

import yaml
from fastapi.testclient import TestClient

from bingo_trivia_system.config import EventPaths
from bingo_trivia_system.models import FREE_CELL, Card, WordBank, WordBankEntry
from bingo_trivia_system.webui.presenter import reset_session

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
