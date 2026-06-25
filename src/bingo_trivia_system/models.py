"""Pydantic data models — single source of truth for the data shapes used
across the cards, simulation, render, email, slides, and web-UI modules.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

GRID_SIZE = 5
FREE_CELL = "FREE"
FREE_ROW = FREE_COL = GRID_SIZE // 2


class Tier(str, Enum):
    """Difficulty tier for a word-bank entry."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class WordBankEntry(BaseModel):
    """A single cell candidate from the word bank.

    Entries with `is_answer = True` may be the correct response to one or
    more questions. Entries that share a `group_id` are alternative valid
    answers to the same question (renders as `N-1`, `N-2`, …).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1)
    tier: Tier
    is_answer: bool = False
    group_id: str | None = None


class WordBank(BaseModel):
    """Collection of word-bank entries used to generate cards."""

    model_config = ConfigDict(extra="forbid")

    entries: list[WordBankEntry]

    @field_validator("entries")
    @classmethod
    def _unique_ids(cls, v: list[WordBankEntry]) -> list[WordBankEntry]:
        ids = [e.id for e in v]
        if len(ids) != len(set(ids)):
            raise ValueError("word bank entry ids must be unique")
        return v

    def by_tier(self, tier: Tier) -> list[WordBankEntry]:
        return [e for e in self.entries if e.tier == tier]

    def by_id(self, entry_id: str) -> WordBankEntry:
        for e in self.entries:
            if e.id == entry_id:
                return e
        raise KeyError(entry_id)


class TierDistribution(BaseModel):
    """Target ratios for each tier on a single card. Must sum to 1.0."""

    model_config = ConfigDict(extra="forbid")

    easy: float = 0.55
    medium: float = 0.30
    hard: float = 0.15

    @field_validator("easy", "medium", "hard")
    @classmethod
    def _non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("tier ratio must be non-negative")
        return v

    def as_dict(self) -> dict[Tier, float]:
        total = self.easy + self.medium + self.hard
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"tier distribution must sum to 1.0 (got {total})")
        return {Tier.EASY: self.easy, Tier.MEDIUM: self.medium, Tier.HARD: self.hard}


WinRule = Literal["line", "blackout", "corners", "x_pattern", "two_lines"]


class Card(BaseModel):
    """A single generated 5x5 bingo card."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    event_id: str
    grid: list[list[str]]  # 5x5 of wordbank entry ids; [2][2] = FREE_CELL
    seed: int

    @field_validator("grid")
    @classmethod
    def _shape(cls, v: list[list[str]]) -> list[list[str]]:
        if len(v) != GRID_SIZE or any(len(r) != GRID_SIZE for r in v):
            raise ValueError(f"grid must be {GRID_SIZE}x{GRID_SIZE}")
        if v[FREE_ROW][FREE_COL] != FREE_CELL:
            raise ValueError("center cell must be FREE")
        flat = [c for row in v for c in row if c != FREE_CELL]
        if len(flat) != len(set(flat)):
            raise ValueError("duplicate entries within a card")
        return v


class Question(BaseModel):
    """A single trivia question with one or more accepted answers."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=1)
    prompt: str
    answer_ids: list[str] = Field(min_length=1)
    image: str | None = None
    image_caption: str | None = None
    timer_seconds: int | None = None
    speaker_notes: str | None = None


class QuestionSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[Question]

    @field_validator("questions")
    @classmethod
    def _unique_indices(cls, v: list[Question]) -> list[Question]:
        idxs = [q.index for q in v]
        if len(idxs) != len(set(idxs)):
            raise ValueError("question indices must be unique")
        return sorted(v, key=lambda q: q.index)


class RosterEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    display_name: str | None = None


class Roster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[RosterEntry]


class Assignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    card_id: UUID
    display_name: str | None = None


class Assignments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    assignments: list[Assignment]

    def by_email(self, email: str) -> Assignment | None:
        for a in self.assignments:
            if a.email.lower() == email.lower():
                return a
        return None

    def by_card_id(self, card_id: UUID | str) -> Assignment | None:
        target = str(card_id)
        for a in self.assignments:
            if str(a.card_id) == target:
                return a
        return None


class SendSettings(BaseModel):
    """Event-local email send settings from `email/send.yaml`."""

    model_config = ConfigDict(extra="forbid")

    bcc_sender: bool = False
    bcc: list[str] = Field(default_factory=list)
    send_delay_seconds: float | None = Field(default=None, ge=0.0)


class EventConfig(BaseModel):
    """Top-level configuration for one event (real or dry-run)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    title: str
    starts_at: datetime | None = None
    num_cards: int = Field(ge=1, default=50)
    win_rule: WinRule = "line"
    tier_distribution: TierDistribution = Field(default_factory=TierDistribution)
    seed: int = 42
    default_timer_seconds: int = 60
    theme: str = "default"
    max_hard_cells: int = 5
    min_answer_coverage: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
