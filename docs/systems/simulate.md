# simulate

`src/bingo_trivia_system/simulate.py`

## What it does

Plays each card forward through `questions` in order, applies the configured
win rule after every question, and records the first question at which the
card hit the win condition.

## Error model

- `error_rate ∈ [0, 1]` — per correct-stamp probability of missing the stamp
  (player error).
- `false_positive_rate ∈ [0, 1]` — per non-answer cell probability of
  stamping in error. Defaults to 0 since it's typically rare; useful for
  stress-testing the "expected winners" defense.

## Determinism

Pure-functional. Given `(cards, questions, win_rule, seed, error_rate,
false_positive_rate, max_questions)`, results are reproducible bit-for-bit.

## Public API

```python
from bingo_trivia_system.simulate import simulate_event, simulate_card, winners_by_question
```

`winners_by_question(...)` is the zero-error projection used by the
presenter's "expected winners by now" panel — it's what answers the question
"if everyone played perfectly, who should have won by question N?".

## Output

`bts simulate` writes one summary per run to `events/<id>/runs/sim-<ts>.json`.
