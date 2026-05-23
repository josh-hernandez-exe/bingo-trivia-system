"""Roster import + email-to-card assignment.

`assign()` is idempotent: existing assignments are preserved, new emails get
unused cards (lowest UUID first for determinism).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from uuid import UUID

from ..models import Assignment, Assignments, Card, Roster, RosterEntry


def load_roster_csv(path: Path) -> Roster:
    entries: list[RosterEntry] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            email = (row.get("email") or "").strip()
            if not email:
                continue
            entries.append(RosterEntry(email=email, display_name=(row.get("display_name") or None)))
    return Roster(entries=entries)


def load_assignments(path: Path, event_id: str) -> Assignments:
    if not path.exists():
        return Assignments(event_id=event_id, assignments=[])
    return Assignments.model_validate_json(path.read_text())


def save_assignments(assignments: Assignments, path: Path) -> None:
    path.write_text(json.dumps(assignments.model_dump(mode="json"), indent=2, sort_keys=True))


def assign(
    event_id: str,
    roster: Roster,
    cards: list[Card],
    existing: Assignments | None = None,
) -> Assignments:
    existing = existing or Assignments(event_id=event_id, assignments=[])
    used: set[UUID] = {a.card_id for a in existing.assignments}
    by_email = {a.email.lower(): a for a in existing.assignments}
    available = sorted([c.id for c in cards if c.id not in used])
    out: list[Assignment] = list(existing.assignments)
    for entry in roster.entries:
        key = entry.email.lower()
        if key in by_email:
            continue
        if not available:
            raise RuntimeError(
                f"ran out of cards: roster has {len(roster.entries)} entries but only "
                f"{len(cards)} cards exist"
            )
        card_id = available.pop(0)
        out.append(Assignment(email=entry.email, card_id=card_id, display_name=entry.display_name))
    return Assignments(event_id=event_id, assignments=out)


def reassign(assignments: Assignments, email: str, cards: list[Card]) -> Assignments:
    # Exclude every currently-assigned card (including the caller's own) so
    # reassignment picks something genuinely new.
    used = {a.card_id for a in assignments.assignments}
    available = sorted([c.id for c in cards if c.id not in used])
    if not available:
        raise RuntimeError("no spare cards available for reassignment")
    new_card = available[0]
    out: list[Assignment] = []
    found = False
    for a in assignments.assignments:
        if a.email.lower() == email.lower():
            out.append(Assignment(email=a.email, card_id=new_card, display_name=a.display_name))
            found = True
        else:
            out.append(a)
    if not found:
        raise KeyError(email)
    return Assignments(event_id=assignments.event_id, assignments=out)
