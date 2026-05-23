"""Play-out simulator with error model and win-rule evaluation.

Pure-functional: no I/O, no global state. Deterministic given
`(cards, questions, win_rule, seed, error_rate, false_positive_rate)`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import median
from uuid import UUID

from . import winrules
from .models import FREE_CELL, GRID_SIZE, Card, Question, WinRule


@dataclass
class CardOutcome:
    card_id: UUID
    won_at_question: int | None  # None = never won inside the run
    stamps: list[tuple[int, int]]  # (row, col) order of stamps applied


@dataclass
class SimulationResult:
    seed: int
    error_rate: float
    false_positive_rate: float
    max_questions: int
    win_rule: WinRule
    outcomes: list[CardOutcome]

    @property
    def winning_steps(self) -> list[int]:
        return [o.won_at_question for o in self.outcomes if o.won_at_question is not None]

    def summary(self) -> dict[str, float | int | None]:
        wins = self.winning_steps
        winners = len(wins)
        first = min(wins) if wins else None
        med = median(wins) if wins else None
        p10 = sorted(wins)[int(0.1 * len(wins))] if wins else None
        p90 = sorted(wins)[int(0.9 * len(wins)) - 1] if wins else None
        return {
            "cards": len(self.outcomes),
            "winners": winners,
            "no_winner_runs": len(self.outcomes) - winners,
            "first_winner_question": first,
            "median_winner_question": med,
            "p10": p10,
            "p90": p90,
        }


def _build_answer_index(card: Card) -> dict[str, list[tuple[int, int]]]:
    idx: dict[str, list[tuple[int, int]]] = {}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cell = card.grid[r][c]
            if cell == FREE_CELL:
                continue
            idx.setdefault(cell, []).append((r, c))
    return idx


def simulate_card(
    card: Card,
    questions: list[Question],
    *,
    win_rule: WinRule,
    rng: random.Random,
    error_rate: float = 0.0,
    false_positive_rate: float = 0.0,
    max_questions: int | None = None,
    all_answer_ids: set[str] | None = None,
) -> CardOutcome:
    """Simulate one card stamping its way through `questions`.

    Returns as soon as the win rule is satisfied. `error_rate` is the
    per-(correct-stamp) probability of missing the stamp; `false_positive_rate`
    is the per-(non-answer-cell-on-this-question) probability of stamping a
    cell that wasn't an answer.
    """

    grid = winrules.empty_grid(free_center=True)
    answer_index = _build_answer_index(card)
    stamps: list[tuple[int, int]] = []
    max_q = max_questions if max_questions is not None else len(questions)
    won_at: int | None = None
    all_answer_ids = all_answer_ids or set()

    for q in questions[:max_q]:
        # Correct stamps for this question (one cell per matching answer id).
        for ans_id in q.answer_ids:
            for r, c in answer_index.get(ans_id, []):
                if grid[r][c]:
                    continue
                if rng.random() < error_rate:
                    continue  # player missed it
                grid[r][c] = True
                stamps.append((r, c))
        # Optional false positives: stamp a non-answer cell.
        if false_positive_rate > 0:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if grid[r][c]:
                        continue
                    cell = card.grid[r][c]
                    if cell in all_answer_ids:
                        continue  # legitimate answer for some other question
                    if rng.random() < false_positive_rate:
                        grid[r][c] = True
                        stamps.append((r, c))
        if winrules.check(win_rule, grid):
            won_at = q.index
            break

    return CardOutcome(card_id=card.id, won_at_question=won_at, stamps=stamps)


def simulate_event(
    cards: list[Card],
    questions: list[Question],
    *,
    win_rule: WinRule,
    seed: int = 0,
    error_rate: float = 0.0,
    false_positive_rate: float = 0.0,
    max_questions: int | None = None,
) -> SimulationResult:
    base_rng = random.Random(seed)
    all_answer_ids = {a for q in questions for a in q.answer_ids}
    outcomes: list[CardOutcome] = []
    for i, card in enumerate(cards):
        # Per-card RNG seed derived from base seed + card index so each card
        # is independent yet reproducible.
        sub = random.Random(base_rng.randint(0, 2**63 - 1) ^ i)
        outcomes.append(
            simulate_card(
                card,
                questions,
                win_rule=win_rule,
                rng=sub,
                error_rate=error_rate,
                false_positive_rate=false_positive_rate,
                max_questions=max_questions,
                all_answer_ids=all_answer_ids,
            )
        )
    return SimulationResult(
        seed=seed,
        error_rate=error_rate,
        false_positive_rate=false_positive_rate,
        max_questions=max_questions or len(questions),
        win_rule=win_rule,
        outcomes=outcomes,
    )


def winners_by_question(
    cards: list[Card],
    questions: list[Question],
    *,
    win_rule: WinRule,
    upto_question: int,
) -> list[tuple[UUID, int]]:
    """Deterministic, no-error projection: which cards should have won by now,
    and at which question. Used by the live presenter's "expected winners" view.
    """

    out: list[tuple[UUID, int]] = []
    for card in cards:
        oc = simulate_card(
            card,
            questions,
            win_rule=win_rule,
            rng=random.Random(0),
            error_rate=0.0,
            false_positive_rate=0.0,
            max_questions=upto_question,
        )
        if oc.won_at_question is not None:
            out.append((card.id, oc.won_at_question))
    out.sort(key=lambda x: x[1])
    return out
