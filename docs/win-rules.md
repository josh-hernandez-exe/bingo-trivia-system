# Win rules

Configured per-event via `event.yaml`'s `win_rule` field.

## Available rules

| Rule | What counts | Typical event length |
|---|---|---|
| `line` | Any single row, column, or diagonal | 30–45 min — gentlest, multiple winners likely |
| `corners` | All four corner cells | 20–30 min — fast, lots of variance |
| `x_pattern` | Both diagonals filled | 30–45 min — feels distinctive |
| `two_lines` | Two or more of {row, col, diagonal} simultaneously | 45–60 min |
| `blackout` | Every cell stamped | 60+ min — final-round only |

The center cell is always pre-stamped as `FREE`.

## Choosing one

Run a simulation against your question list and pick the rule whose
**median winning question** lands at roughly 60% of the question list
length. That leaves headroom for the inevitable retries and bingo-checks.

```bash
EVENT_DEFAULT=my-event uv run bts simulate --runs 500 --error-rate 0.07
```

Re-run with a different `win_rule` to compare.

## Adding a custom rule

See [`docs/systems/winrules.md`](systems/winrules.md). It's three small
edits: a pure function, a dispatcher registration, a Literal entry, and a
test.
