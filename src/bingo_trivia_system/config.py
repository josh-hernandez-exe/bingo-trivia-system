"""Event-folder discovery + path resolution.

Every CLI / web-UI operation is scoped to one event ID; this module is the
only place that maps `<event-id>` to filesystem paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .models import EventConfig

load_dotenv()

DEFAULT_EVENTS_ROOT = Path(os.environ.get("BTS_EVENTS_ROOT", "events")).resolve()


def resolve_event_id(event: str | None) -> str:
    """Resolve event id from arg or `EVENT_DEFAULT` env var."""

    if event:
        return event
    default = os.environ.get("EVENT_DEFAULT")
    if not default:
        raise ValueError(
            "no event id provided and EVENT_DEFAULT is unset — "
            "pass --event <id> or set EVENT_DEFAULT in your .env"
        )
    return default


@dataclass(frozen=True)
class EventPaths:
    """All filesystem paths derived from one event id."""

    event_id: str
    root: Path

    @property
    def event_yaml(self) -> Path:
        return self.root / "event.yaml"

    @property
    def wordbank_yaml(self) -> Path:
        return self.root / "wordbank.yaml"

    @property
    def questions_yaml(self) -> Path:
        return self.root / "questions.yaml"

    @property
    def roster_csv(self) -> Path:
        return self.root / "roster.csv"

    @property
    def assignments_json(self) -> Path:
        return self.root / "assignments.json"

    @property
    def cards_dir(self) -> Path:
        return self.root / "cards"

    @property
    def cards_pdf_dir(self) -> Path:
        return self.root / "cards" / "pdf"

    @property
    def images_dir(self) -> Path:
        return self.root / "images"

    @property
    def slides_dir(self) -> Path:
        return self.root / "slides"

    @property
    def runs_dir(self) -> Path:
        return self.root / "runs"

    def ensure_dirs(self) -> None:
        for d in (
            self.cards_dir,
            self.cards_pdf_dir,
            self.images_dir,
            self.slides_dir,
            self.runs_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


def event_paths(event: str | None = None, root: Path | None = None) -> EventPaths:
    eid = resolve_event_id(event)
    base = Path(root) if root else DEFAULT_EVENTS_ROOT
    return EventPaths(event_id=eid, root=base / eid)


def load_event_config(paths: EventPaths) -> EventConfig:
    if not paths.event_yaml.exists():
        raise FileNotFoundError(f"event config not found: {paths.event_yaml}")
    data = yaml.safe_load(paths.event_yaml.read_text())
    data.setdefault("id", paths.event_id)
    return EventConfig.model_validate(data)


def list_events(root: Path | None = None) -> list[str]:
    base = Path(root) if root else DEFAULT_EVENTS_ROOT
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and (p / "event.yaml").exists())
