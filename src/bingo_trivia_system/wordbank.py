"""Word-bank loading + validation + tier-pool helpers."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from .models import GRID_SIZE, Tier, WordBank, WordBankEntry


def load_wordbank(path: Path) -> WordBank:
    data = yaml.safe_load(path.read_text())
    if isinstance(data, list):
        data = {"entries": data}
    return WordBank.model_validate(data)


def validate_for_cards(
    wordbank: WordBank,
    *,
    num_cards: int,
    tier_targets: dict[Tier, float],
    cells_per_card: int = GRID_SIZE * GRID_SIZE - 1,
) -> None:
    """Raise ValueError if the bank cannot support `num_cards` distinct cards.

    The required pool size for a tier is large enough that we can sample
    `ceil(cells_per_card * ratio)` cells per card without rejection sampling
    blowing up. We require at least that many entries per tier.
    """

    counts = Counter(e.tier for e in wordbank.entries)
    for tier, ratio in tier_targets.items():
        per_card = max(1, round(cells_per_card * ratio))
        if counts[tier] < per_card:
            raise ValueError(
                f"tier {tier.value!r} has {counts[tier]} entries; need at least "
                f"{per_card} to fill a {cells_per_card}-cell card with ratio {ratio}"
            )
    if sum(counts.values()) < cells_per_card:
        raise ValueError(
            f"word bank has {sum(counts.values())} entries; need at least {cells_per_card} "
            f"to fill a single card"
        )


def answer_entries(wordbank: WordBank) -> list[WordBankEntry]:
    return [e for e in wordbank.entries if e.is_answer]
