# wordbank

`src/bingo_trivia_system/wordbank.py`

Loads and validates `events/<id>/wordbank.yaml`.

## Schema

```yaml
entries:
  - { id: red, text: "Red", tier: easy, is_answer: true }
  - { id: oct, text: "Octagon", tier: medium, is_answer: true, group_id: q6 }
```

- `id` — short, unique, used as the grid cell identifier.
- `tier` — `easy | medium | hard`. Drives sampling weight in `cards.py`.
- `is_answer` — `true` if this entry is the correct response to some question.
- `group_id` (optional) — ties multiple alternative answers to one question.
  Renders as `N-1`, `N-2`, … on stamped cards.

## Validation

`validate_for_cards(bank, num_cards, tier_targets)` raises `ValueError` if
any tier has too few entries to fill a card at the requested ratio.
