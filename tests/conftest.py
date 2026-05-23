"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bingo_trivia_system.models import EventConfig, QuestionSet, WordBank

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = REPO_ROOT / "events" / "example-shapes-and-colors"


@pytest.fixture
def sample_event() -> EventConfig:
    return EventConfig.model_validate(yaml.safe_load((SAMPLE / "event.yaml").read_text()))


@pytest.fixture
def sample_wordbank() -> WordBank:
    return WordBank.model_validate(yaml.safe_load((SAMPLE / "wordbank.yaml").read_text()))


@pytest.fixture
def sample_questions() -> QuestionSet:
    return QuestionSet.model_validate(yaml.safe_load((SAMPLE / "questions.yaml").read_text()))
