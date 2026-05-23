from pathlib import Path

import pytest
import yaml

from bingo_trivia_system.models import Tier
from bingo_trivia_system.wordbank import load_wordbank, validate_for_cards


def test_loads_sample_wordbank():
    wb = load_wordbank(Path("events/example-shapes-and-colors/wordbank.yaml"))
    assert any(e.tier == Tier.HARD for e in wb.entries)


def test_unique_ids_enforced(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        yaml.safe_dump(
            {
                "entries": [
                    {"id": "x", "text": "a", "tier": "easy"},
                    {"id": "x", "text": "b", "tier": "easy"},
                ]
            }
        )
    )
    with pytest.raises(Exception):
        load_wordbank(bad)


def test_validate_for_cards_too_few_easy(sample_wordbank):
    targets = {Tier.EASY: 0.99, Tier.MEDIUM: 0.005, Tier.HARD: 0.005}
    with pytest.raises(ValueError):
        # 24 cells * 0.99 = ~24 easy cells per card; bank has only 16 easy.
        validate_for_cards(sample_wordbank, num_cards=1, tier_targets=targets)
