# cards

`src/bingo_trivia_system/cards.py`

## What it guarantees

- Given the same `(event.id, event.seed, event.num_cards, wordbank)`, output
  is **byte-identical** across runs and across machines.
- Per-card RNG is seeded from `sha256(event.seed:card_index)` so adding cards
  to a batch (`--count` bumped) does not reshuffle existing cards.
- Each card is a valid `Card` model:
  - 5×5 grid
  - center cell is `FREE`
  - all 24 non-FREE entries are unique within the card
- The number of cells per tier is derived from `event.tier_distribution`
  with fractional remainders distributed largest-first.
- `event.max_hard_cells` caps the number of hard-tier cells per card;
  overflow is reassigned to the medium tier.

## Public API

```python
from bingo_trivia_system.cards import generate_cards, write_cards, read_cards
```

## File layout produced

```
events/<id>/cards/<uuid>.json
```

Each JSON file is a serialised `Card` model.

## Determinism contract

Anything in this module that consumes randomness MUST take a seed and produce
the same output across runs. The test `tests/test_cards.py::test_generate_cards_deterministic`
enforces this.
