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

## Q35-Q40 planning comparison

The June 16, 2026 planning run was updated for a 45-question pool. The target is
at least one winner between Q35 and Q40 for both 40 and 100 participants.

The best tested ordering model is:

- Q1-Q35: regular questions, but hold back 10 real answer IDs so no card can
	complete `blackout` too early.
- Q36-Q40: introduce those 10 delayed answer IDs, each in two different
	multi-answer questions.
- Q41-Q45: reserve full-pool redundancy questions in case the group needs more
	recovery time.

The demo word bank has no decoy cells. Every card cell is a legitimate answer
somewhere in the 45-question pool. Adding cells that never appear as answers
would make `blackout` impossible for any card containing those cells.

The `five_lines` rule below is an analysis-only candidate, not a built-in event
rule yet. It means any 5 distinct completed lines from the 5 rows, 5 columns,
and 2 diagonals. Any horizontal, vertical, and diagonal combination counts.

The table used 2,000 full-event Monte Carlo runs per row. `P by Q35/Q40/Q45` is
the chance at least one participant has won by that point.

| Participants | Rule | Miss rate | P by Q35 | P by Q40 | P by Q45 | First winner p10 | Median | p90 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 40 | `five_lines` | 10% | 0.0% | 100.0% | 100.0% | Q36 | Q36 | Q36 |
| 40 | `five_lines` | 15% | 0.0% | 100.0% | 100.0% | Q36 | Q36 | Q36 |
| 40 | `five_lines` | 20% | 0.0% | 100.0% | 100.0% | Q36 | Q36 | Q36 |
| 40 | `x_pattern` | 10% | 97.1% | 100.0% | 100.0% | Q21 | Q22 | Q25 |
| 40 | `x_pattern` | 15% | 88.4% | 100.0% | 100.0% | Q21 | Q23 | Q36 |
| 40 | `x_pattern` | 20% | 75.4% | 100.0% | 100.0% | Q21 | Q23 | Q36 |
| 40 | `blackout` | 10% | 0.0% | 100.0% | 100.0% | Q38 | Q38 | Q39 |
| 40 | `blackout` | 15% | 0.0% | 99.95% | 100.0% | Q38 | Q39 | Q39 |
| 40 | `blackout` | 20% | 0.0% | 96.65% | 100.0% | Q38 | Q39 | Q40 |
| 100 | `five_lines` | 10% | 97.8% | 100.0% | 100.0% | Q21 | Q24 | Q29 |
| 100 | `five_lines` | 15% | 88.0% | 100.0% | 100.0% | Q22 | Q24 | Q36 |
| 100 | `five_lines` | 20% | 67.85% | 100.0% | 100.0% | Q24 | Q31 | Q36 |
| 100 | `x_pattern` | 10% | 98.95% | 100.0% | 100.0% | Q21 | Q22 | Q24 |
| 100 | `x_pattern` | 15% | 93.85% | 100.0% | 100.0% | Q21 | Q23 | Q31 |
| 100 | `x_pattern` | 20% | 84.3% | 100.0% | 100.0% | Q21 | Q23 | Q36 |
| 100 | `blackout` | 10% | 0.0% | 100.0% | 100.0% | Q38 | Q38 | Q39 |
| 100 | `blackout` | 15% | 0.0% | 100.0% | 100.0% | Q38 | Q38 | Q39 |
| 100 | `blackout` | 20% | 0.0% | 100.0% | 100.0% | Q38 | Q39 | Q39 |

For this goal, `blackout` with delayed answer coverage is the best fit. It
prevents early wins, lands the first winner around Q38-Q39, and remains at least
96.65% likely by Q40 even for 40 participants with a 20% missed-stamp rate.
`five_lines` is reliable but tends to fire immediately when the delayed answers
begin at Q36. `x_pattern` is too sensitive to lucky layouts and can produce
winners before Q35, especially as attendance grows.

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
