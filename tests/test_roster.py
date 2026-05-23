from uuid import uuid4

import pytest

from bingo_trivia_system.email.roster import assign, reassign
from bingo_trivia_system.models import Card, Roster, RosterEntry


def _card():
    grid = [["x" for _ in range(5)] for _ in range(5)]
    grid[2][2] = "FREE"
    # uniqueness: just stamp ids
    counter = 0
    for r in range(5):
        for c in range(5):
            if grid[r][c] == "FREE":
                continue
            grid[r][c] = f"e{counter}"
            counter += 1
    return Card(id=uuid4(), event_id="evt", grid=grid, seed=0)


def test_assign_is_idempotent():
    cards = [_card() for _ in range(5)]
    roster = Roster(
        entries=[RosterEntry(email="a@example.com"), RosterEntry(email="b@example.com")]
    )
    a1 = assign("evt", roster, cards)
    a2 = assign("evt", roster, cards, existing=a1)
    assert [x.email for x in a1.assignments] == [x.email for x in a2.assignments]
    assert [x.card_id for x in a1.assignments] == [x.card_id for x in a2.assignments]


def test_assign_fails_when_too_few_cards():
    cards = [_card()]
    roster = Roster(
        entries=[RosterEntry(email="a@example.com"), RosterEntry(email="b@example.com")]
    )
    with pytest.raises(RuntimeError):
        assign("evt", roster, cards)


def test_reassign_picks_unused_card():
    cards = [_card() for _ in range(3)]
    roster = Roster(entries=[RosterEntry(email="a@example.com")])
    a1 = assign("evt", roster, cards)
    original = a1.assignments[0].card_id
    a2 = reassign(a1, "a@example.com", cards)
    assert a2.assignments[0].card_id != original
