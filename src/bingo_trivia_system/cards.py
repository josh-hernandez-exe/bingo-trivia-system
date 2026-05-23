"""Deterministic, tier-weighted card generation.

`generate_cards(event, wordbank)` is byte-identical across runs given the
same event seed. Per-card RNG is seeded from `(event.seed, card_index)` so
that adding cards to a batch never reshuffles existing cards.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

from .models import (
    FREE_CELL,
    FREE_COL,
    FREE_ROW,
    GRID_SIZE,
    Card,
    EventConfig,
    Tier,
    WordBank,
    WordBankEntry,
)

CELLS_PER_CARD = GRID_SIZE * GRID_SIZE - 1  # 24 (center is FREE)


def _seed_for(event_seed: int, index: int) -> int:
    digest = hashlib.sha256(f"{event_seed}:{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _card_uuid(event_id: str, event_seed: int, index: int) -> UUID:
    raw = hashlib.sha256(f"{event_id}:{event_seed}:{index}".encode()).digest()
    # Stamp UUID v4 variant bits so it's a valid UUID4 string.
    b = bytearray(raw[:16])
    b[6] = (b[6] & 0x0F) | 0x40
    b[8] = (b[8] & 0x3F) | 0x80
    return UUID(bytes=bytes(b))


def _tier_quotas(event: EventConfig) -> dict[Tier, int]:
    ratios = event.tier_distribution.as_dict()
    raw = {t: CELLS_PER_CARD * r for t, r in ratios.items()}
    quotas = {t: int(v) for t, v in raw.items()}
    # Distribute remaining slots to tiers with the largest fractional remainder.
    remaining = CELLS_PER_CARD - sum(quotas.values())
    leftovers = sorted(raw.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True)
    i = 0
    while remaining > 0 and leftovers:
        tier, _ = leftovers[i % len(leftovers)]
        quotas[tier] += 1
        remaining -= 1
        i += 1
    # Cap hard cells.
    if quotas.get(Tier.HARD, 0) > event.max_hard_cells:
        overflow = quotas[Tier.HARD] - event.max_hard_cells
        quotas[Tier.HARD] = event.max_hard_cells
        quotas[Tier.MEDIUM] = quotas.get(Tier.MEDIUM, 0) + overflow
    return quotas


def _pick_for_tier(rng: random.Random, pool: list[WordBankEntry], k: int) -> list[WordBankEntry]:
    if k > len(pool):
        raise ValueError(f"need {k} entries from tier pool of size {len(pool)}")
    return rng.sample(pool, k)


def _build_grid(rng: random.Random, picks: Iterable[WordBankEntry]) -> list[list[str]]:
    ids = [e.id for e in picks]
    rng.shuffle(ids)
    grid = [[""] * GRID_SIZE for _ in range(GRID_SIZE)]
    it = iter(ids)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if r == FREE_ROW and c == FREE_COL:
                grid[r][c] = FREE_CELL
            else:
                grid[r][c] = next(it)
    return grid


def generate_cards(event: EventConfig, wordbank: WordBank) -> list[Card]:
    """Generate `event.num_cards` deterministic cards from the word bank."""

    quotas = _tier_quotas(event)
    pools: dict[Tier, list[WordBankEntry]] = {t: wordbank.by_tier(t) for t in Tier}

    cards: list[Card] = []
    for i in range(event.num_cards):
        seed = _seed_for(event.seed, i)
        rng = random.Random(seed)
        picks: list[WordBankEntry] = []
        # Iterate tiers in deterministic order.
        for tier in (Tier.EASY, Tier.MEDIUM, Tier.HARD):
            k = quotas.get(tier, 0)
            if k:
                picks.extend(_pick_for_tier(rng, list(pools[tier]), k))
        grid = _build_grid(rng, picks)
        card = Card(
            id=_card_uuid(event.id, event.seed, i),
            event_id=event.id,
            grid=grid,
            seed=seed,
        )
        cards.append(card)
    return cards


def write_cards(cards: list[Card], cards_dir: Path) -> list[Path]:
    cards_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for c in cards:
        path = cards_dir / f"{c.id}.json"
        path.write_text(json.dumps(c.model_dump(mode="json"), indent=2, sort_keys=True))
        written.append(path)
    return written


def read_cards(cards_dir: Path) -> list[Card]:
    if not cards_dir.exists():
        return []
    out: list[Card] = []
    for p in sorted(cards_dir.glob("*.json")):
        out.append(Card.model_validate_json(p.read_text()))
    return out
