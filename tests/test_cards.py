from __future__ import annotations

from collections import Counter

from bingo_trivia_system.cards import generate_cards
from bingo_trivia_system.models import FREE_CELL, FREE_COL, FREE_ROW, GRID_SIZE


def test_generate_cards_deterministic(sample_event, sample_wordbank):
    a = generate_cards(sample_event, sample_wordbank)
    b = generate_cards(sample_event, sample_wordbank)
    assert [c.model_dump(mode="json") for c in a] == [c.model_dump(mode="json") for c in b]


def test_card_invariants(sample_event, sample_wordbank):
    cards = generate_cards(sample_event, sample_wordbank)
    assert len(cards) == sample_event.num_cards
    for card in cards:
        flat = [cell for row in card.grid for cell in row]
        assert card.grid[FREE_ROW][FREE_COL] == FREE_CELL
        assert len(flat) == GRID_SIZE * GRID_SIZE
        # All non-FREE entries are unique within the card.
        non_free = [c for c in flat if c != FREE_CELL]
        assert len(non_free) == len(set(non_free))


def test_card_ids_stable_across_runs(sample_event, sample_wordbank):
    a = generate_cards(sample_event, sample_wordbank)
    b = generate_cards(sample_event, sample_wordbank)
    assert [c.id for c in a] == [c.id for c in b]


def test_seed_change_changes_cards(sample_event, sample_wordbank):
    other = sample_event.model_copy(update={"seed": sample_event.seed + 1})
    a = generate_cards(sample_event, sample_wordbank)
    b = generate_cards(other, sample_wordbank)
    assert [c.id for c in a] != [c.id for c in b]


def test_tier_distribution_within_tolerance(sample_event, sample_wordbank):
    cards = generate_cards(sample_event, sample_wordbank)
    tier_of = {e.id: e.tier.value for e in sample_wordbank.entries}
    total = Counter()
    for c in cards:
        for row in c.grid:
            for cell in row:
                if cell == FREE_CELL:
                    continue
                total[tier_of[cell]] += 1
    grand = sum(total.values())
    easy_ratio = total["easy"] / grand
    # We requested 55% easy; allow ±10% absolute tolerance for small batches.
    assert 0.45 < easy_ratio < 0.65, total
