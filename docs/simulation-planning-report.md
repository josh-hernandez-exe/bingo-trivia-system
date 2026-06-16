# Simulation planning report

This report summarizes the June 16, 2026 simulation pass for planning a
1-hour trivia bingo meeting with about 40 minutes of actual game time.

The current planning goal is:

- Prepare a 45-question pool.
- Expect to ask about 35-40 questions live.
- Make every card cell a real answer somewhere in the 45-question pool.
- Have a high likelihood of at least one winner between Q35 and Q40.
- Support the expected attendance range: about 40 people minimum and 100 people
  as the upper planning bound.

## Meeting assumptions

- Calendar block: 60 minutes.
- Setup and closing discussion: about 10 minutes at the beginning and 10
  minutes at the end.
- Game time: about 40 minutes.
- Realistic pacing: 45-60 seconds per question, including time for players to
  hear the question, think of the answer, and search their card.

For planning, treat 40 asked questions as the practical live target. The extra
questions in the 45-question pool are useful for recovery, tie-breakers,
skipped questions, and late-game padding.

## Simulation inputs

The updated projection uses the demo event as the shape of the system, but
models a 45-question target ordering rather than the demo's original
35-question order.

- Event shape: `example-shapes-and-colors`
- Attendance tested: 40 and 100 generated cards
- Questions modeled: 45
- Card shape: 5x5 with a pre-stamped center `FREE` cell
- Tier distribution: 55% easy, 30% medium, 15% hard
- Approximate cells per card: 13 easy, 7 medium, 4 hard
- Error model: missed correct stamps only
- Sample size: 2,000 full-event Monte Carlo runs per row
- Decoy cells: none. Every card cell is a legitimate answer somewhere in the
  45-question pool.

One full-event run simulates all cards for that event once, not one card in
isolation.

The current simulator's `error_rate` means: for each correct cell that a player
could stamp, this is the probability they miss it. For this no-decoy word bank,
`false_positive_rate` is not a useful proxy for players stamping the wrong
future answer, because all card cells are legitimate answer IDs somewhere in
the question set.

## 45-question ordering model

The ordering matters as much as the win rule. If the first 35 questions already
cover every card answer, then `blackout` can happen before Q35. To target a
winner between Q35 and Q40, the simulated 45-question pool uses this shape:

- Q1-Q35: regular questions, but intentionally hold back 10 real answer IDs.
- Q36-Q40: introduce those 10 delayed answer IDs; each delayed answer appears
  in two different multi-answer questions in this range.
- Q41-Q45: full-pool redundancy questions that give players extra recovery
  chances if they missed correct stamps earlier.

This keeps every card cell answerable while preventing `blackout` from being
available too early.

## Recommendation

Use `blackout` as the main win condition if the Q35-Q40 target matters.

With the 45-question target ordering, `blackout` has no winners by Q35, reaches
at least 96.65% chance of a winner by Q40 for both 40 and 100 participants at
10-20% missed stamps, and has a median first winner around Q38-Q39.

Do not use `x_pattern` as the main rule for this target. With 40-100 cards in
play, lucky layouts can produce winners well before Q35. `five_lines` is much
more reliable than `x_pattern`, but in this ordering it tends to fire right when
the delayed answer band starts around Q36.

## Key results

`P by Q35/Q40/Q45` is the chance that at least one participant has won by that
question. `Avg winners by Q45` is the average number of winning cards by the
end of the 45-question pool.

| Participants | Rule | Miss rate | P by Q35 | P by Q40 | P by Q45 | First winner p10 | Median | p90 | Avg winners by Q45 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 40 | `five_lines` | 10% | 0.0% | 100.0% | 100.0% | Q36 | Q36 | Q36 | 40.00 |
| 40 | `five_lines` | 15% | 0.0% | 100.0% | 100.0% | Q36 | Q36 | Q36 | 40.00 |
| 40 | `five_lines` | 20% | 0.0% | 100.0% | 100.0% | Q36 | Q36 | Q36 | 39.98 |
| 40 | `x_pattern` | 10% | 97.1% | 100.0% | 100.0% | Q21 | Q22 | Q25 | 38.63 |
| 40 | `x_pattern` | 15% | 88.4% | 100.0% | 100.0% | Q21 | Q23 | Q36 | 36.86 |
| 40 | `x_pattern` | 20% | 75.4% | 100.0% | 100.0% | Q21 | Q23 | Q36 | 34.19 |
| 40 | `blackout` | 10% | 0.0% | 100.0% | 100.0% | Q38 | Q38 | Q39 | 36.07 |
| 40 | `blackout` | 15% | 0.0% | 99.95% | 100.0% | Q38 | Q39 | Q39 | 31.25 |
| 40 | `blackout` | 20% | 0.0% | 96.65% | 100.0% | Q38 | Q39 | Q40 | 24.93 |
| 100 | `five_lines` | 10% | 97.8% | 100.0% | 100.0% | Q21 | Q24 | Q29 | 100.00 |
| 100 | `five_lines` | 15% | 88.0% | 100.0% | 100.0% | Q22 | Q24 | Q36 | 99.99 |
| 100 | `five_lines` | 20% | 67.85% | 100.0% | 100.0% | Q24 | Q31 | Q36 | 99.94 |
| 100 | `x_pattern` | 10% | 98.95% | 100.0% | 100.0% | Q21 | Q22 | Q24 | 96.62 |
| 100 | `x_pattern` | 15% | 93.85% | 100.0% | 100.0% | Q21 | Q23 | Q31 | 92.04 |
| 100 | `x_pattern` | 20% | 84.3% | 100.0% | 100.0% | Q21 | Q23 | Q36 | 85.37 |
| 100 | `blackout` | 10% | 0.0% | 100.0% | 100.0% | Q38 | Q38 | Q39 | 90.19 |
| 100 | `blackout` | 15% | 0.0% | 100.0% | 100.0% | Q38 | Q38 | Q39 | 78.07 |
| 100 | `blackout` | 20% | 0.0% | 100.0% | 100.0% | Q38 | Q39 | Q39 | 62.22 |

Key read:

- `blackout` with delayed answer coverage is the best fit for a Q35-Q40 first
  winner.
- The 45-question pool must include late answer coverage; simply adding 10
  unrelated extra questions is not enough to control the finish window.
- More participants increase the chance of lucky early layouts, which is why
  `x_pattern` and `five_lines` can drift earlier at 100 cards.
- Q41-Q45 still matter: they make every tested `blackout` scenario reach 100%
  by Q45, even at 20% missed stamps.

## Question-count target

For a 40-minute game window:

| Seconds per question | Theoretical max questions | Practical target |
|---:|---:|---:|
| 45 | 53 | 40-45 |
| 50 | 48 | 38-42 |
| 60 | 40 | 35-40 |

Recommended authoring target:

- Write 45 real, answer-bearing questions.
- Plan the live game around 35-40 asked questions.
- Put the `blackout` unlock band at Q36-Q40.
- Keep Q41-Q45 as recovery, tie-breaker, or showcase material.

## Answer distribution guidance

Keep the card distribution close to the current shape:

- Easy: about 55% of card cells
- Medium: about 30% of card cells
- Hard: about 15% of card cells

For a 5x5 card with a free center, that means about:

- 13 easy cells
- 7 medium cells
- 4 hard cells

Question ordering guidance:

- Every card cell must appear as an answer somewhere in the 45-question pool.
- Do not use decoy/non-answer cells on player cards if `blackout` is the goal.
- Hold back about 10 real answer IDs until Q36-Q40.
- Give each held-back answer two separate stamp opportunities during Q36-Q40.
- Use Q41-Q45 to provide broad redundancy across the full answer pool.

## How to verify with the CLI

After you author the real 45-question event file, generate cards for the group
size you want to test and run the built-in simulator:

```bash
EVENT_DEFAULT=my-event uv run bts cards generate --count 40
EVENT_DEFAULT=my-event uv run bts simulate --runs 500 --error-rate 0.15 --max-questions 45

EVENT_DEFAULT=my-event uv run bts cards generate --count 100
EVENT_DEFAULT=my-event uv run bts simulate --runs 500 --error-rate 0.15 --max-questions 45
```

The CLI uses the event's configured `win_rule` from `event.yaml`. Set it to
`blackout` for the recommended plan. The CLI can verify the real authored event;
the analysis-only `five_lines` rule requires the Python script below or a future
custom win-rule implementation.

## Reproduce the projection

Run this script from the repository root to reproduce the 45-question target
ordering model used above. It builds synthetic question order from the demo word
bank so you can inspect the math before the real 45 prompts are written.

```bash
uv run python - <<'PY'
from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean
import random
import yaml

from bingo_trivia_system.cards import generate_cards
from bingo_trivia_system.models import FREE_CELL, GRID_SIZE, EventConfig, Question, QuestionSet, WordBank

root = Path("events/example-shapes-and-colors")
event = EventConfig.model_validate(yaml.safe_load((root / "event.yaml").read_text()))
wordbank = WordBank.model_validate(yaml.safe_load((root / "wordbank.yaml").read_text()))
base_questions = QuestionSet.model_validate(yaml.safe_load((root / "questions.yaml").read_text())).questions
answer_ids = [entry.id for entry in wordbank.entries if entry.is_answer]
counts = Counter(answer_id for question in base_questions for answer_id in question.answer_ids)
late_ids = sorted(answer_ids, key=lambda answer_id: (counts[answer_id], answer_id))[:10]
early_ids = [answer_id for answer_id in answer_ids if answer_id not in set(late_ids)]

def round_robin(items: list[str], groups: int) -> list[list[str]]:
    out = [[] for _ in range(groups)]
    for index, item in enumerate(items):
        out[index % groups].append(item)
    return out

def late_double_groups(items: list[str], groups: int) -> list[list[str]]:
    out = round_robin(items, groups)
    for index, item in enumerate(items):
        out[(index + 1) % groups].append(item)
    return out

questions = []
for index in range(35):
    questions.append(Question(index=index + 1, prompt=f"Early {index + 1}", answer_ids=[early_ids[index % len(early_ids)]]))
for index, group in enumerate(late_double_groups(late_ids, 5)):
    questions.append(Question(index=36 + index, prompt=f"Late {index + 1}", answer_ids=group))
for index, group in enumerate(round_robin(answer_ids, 5)):
    questions.append(Question(index=41 + index, prompt=f"Recovery {index + 1}", answer_ids=group))

def bit(row: int, col: int) -> int:
    return 1 << (row * GRID_SIZE + col)

free = bit(2, 2)
line_masks = [sum(bit(row, col) for col in range(GRID_SIZE)) for row in range(GRID_SIZE)]
line_masks += [sum(bit(row, col) for row in range(GRID_SIZE)) for col in range(GRID_SIZE)]
diag_a = sum(bit(i, i) for i in range(GRID_SIZE))
diag_b = sum(bit(i, GRID_SIZE - 1 - i) for i in range(GRID_SIZE))
line_masks += [diag_a, diag_b]
x_pattern = diag_a | diag_b
blackout = sum(bit(row, col) for row in range(GRID_SIZE) for col in range(GRID_SIZE))

def completed_lines(mask: int) -> int:
    return sum((mask & line) == line for line in line_masks)

def is_win(rule: str, mask: int) -> bool:
    if rule == "five_lines":
        return completed_lines(mask) >= 5
    if rule == "x_pattern":
        return (mask & x_pattern) == x_pattern
    if rule == "blackout":
        return (mask & blackout) == blackout
    raise ValueError(rule)

def apply_misses(mask: int, correct: int, rng: random.Random, miss_rate: float) -> int:
    remaining = correct & ~mask
    while remaining:
        stamp = remaining & -remaining
        if rng.random() >= miss_rate:
            mask |= stamp
        remaining ^= stamp
    return mask

def prepare(cards):
    output = []
    for card in cards:
        answer_to_mask = {}
        for row_index, row in enumerate(card.grid):
            for col_index, answer_id in enumerate(row):
                if answer_id != FREE_CELL:
                    answer_to_mask[answer_id] = answer_to_mask.get(answer_id, 0) | bit(row_index, col_index)
        output.append([sum(answer_to_mask.get(answer_id, 0) for answer_id in question.answer_ids) for question in questions])
    return output

def simulate(rule: str, miss_rate: float, seed: int, question_masks_by_card):
    base_rng = random.Random(seed)
    outcomes = []
    for card_index, question_masks in enumerate(question_masks_by_card):
        rng = random.Random(base_rng.randint(0, 2**63 - 1) ^ card_index)
        mask = free
        won_at = None
        for question_index, question_mask in enumerate(question_masks, start=1):
            mask = apply_misses(mask, question_mask, rng, miss_rate)
            if is_win(rule, mask):
                won_at = questions[question_index - 1].index
                break
        outcomes.append(won_at)
    return outcomes

def percentile(values: list[int], q: float) -> str:
    if not values:
        return "NA"
    values = sorted(values)
    return str(values[round((len(values) - 1) * q)])

def summarize(rows, cap: int):
    firsts = []
    counts = []
    for outcomes in rows:
        wins = [outcome for outcome in outcomes if outcome is not None and outcome <= cap]
        counts.append(len(wins))
        if wins:
            firsts.append(min(wins))
    return len(firsts) / len(rows), percentile(firsts, 0.1), percentile(firsts, 0.5), percentile(firsts, 0.9), mean(counts)

runs = 2000
print("participants rule miss P_by_Q35 P_by_Q40 P_by_Q45 p10 median p90 avg_winners_Q45")
for participants in [40, 100]:
    cards = generate_cards(event.model_copy(update={"num_cards": participants}), wordbank)
    question_masks_by_card = prepare(cards)
    for miss_rate in [0.10, 0.15, 0.20]:
        for rule in ["five_lines", "x_pattern", "blackout"]:
            rows = [simulate(rule, miss_rate, seed, question_masks_by_card) for seed in range(runs)]
            p35, *_ = summarize(rows, 35)
            p40, *_ = summarize(rows, 40)
            p45, p10, p50, p90, average = summarize(rows, 45)
            print(f"{participants:3d} {rule:10s} {miss_rate:0.2f} {p35:0.4f} {p40:0.4f} {p45:0.4f} {p10:>3} {p50:>3} {p90:>3} {average:6.2f}")
        print()
PY
```

## Caveats

- These numbers are based on the demo event's word-bank size and tier mix. Re-
  run the simulation after replacing the demo questions with real event
  questions.
- The miss-rate model is useful but simplified. Real mistakes include missed
  stamps, misread answers, delayed searching, and incorrect stamps.
- The 45-question ordering model assumes some multi-answer questions in Q36-Q45.
  If every question has exactly one answer, the Q35-Q40 confidence will be lower.
- The live experience should still leave room for repeats, clarification, and
  winner verification.
