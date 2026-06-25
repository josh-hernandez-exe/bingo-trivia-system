"""Presenter-mode state machine + Server-Sent Events broadcaster.

State is in-process (single-presenter assumption). Every state change is
persisted to `runs/presenter-<ts>.json` so a refresh restores exactly the
last state.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import UUID


@dataclass
class PresenterState:
    event_id: str
    current_q_index: int = 0  # 0 = pre-start
    revealed: bool = False
    paused: bool = False
    started_at: float | None = None
    timer_seconds: int = 60
    timer_remaining: int = 60
    show_card_id: str | None = None
    show_answers: bool = False
    answer_pass: bool = False
    finished: bool = False


class PresenterSession:
    """Holds the live presenter state for one event and notifies subscribers."""

    def __init__(self, event_id: str, persist_dir: Path) -> None:
        self.state = PresenterState(event_id=event_id)
        self._subscribers: list[asyncio.Queue[str]] = []
        self._persist_dir = persist_dir
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._persist_file = self._persist_dir / f"presenter-{int(time.time())}.json"

    # ---- state mutations -------------------------------------------------
    def advance(self) -> None:
        self.state.current_q_index += 1
        self.state.revealed = False
        self.state.paused = False
        self.state.started_at = time.time()
        self.state.timer_remaining = self.state.timer_seconds
        self.state.show_card_id = None
        self.state.show_answers = False
        self._broadcast()

    def _current_timer_remaining(self) -> int:
        if self.state.current_q_index <= 0 or self.state.paused or self.state.started_at is None:
            return self.state.timer_remaining
        elapsed = max(0, int(time.time() - self.state.started_at))
        return max(0, self.state.timer_remaining - elapsed)

    def back(self) -> None:
        self.state.current_q_index = max(0, self.state.current_q_index - 1)
        self.state.revealed = False
        self._broadcast()

    def toggle_reveal(self) -> None:
        self.state.revealed = not self.state.revealed
        self._broadcast()

    def toggle_answer_pass(self) -> None:
        self.state.answer_pass = not self.state.answer_pass
        self._broadcast()

    def pause(self) -> None:
        if self.state.paused:
            self.state.paused = False
            self.state.started_at = time.time()
        else:
            self.state.timer_remaining = self._current_timer_remaining()
            self.state.paused = True
            self.state.started_at = None
        self._broadcast()

    def add_time(self, seconds: int = 30) -> None:
        self.state.timer_remaining = self._current_timer_remaining() + seconds
        if not self.state.paused and self.state.current_q_index > 0:
            self.state.started_at = time.time()
        self._broadcast()

    def show_card(self, card_id: UUID | str) -> None:
        self.state.show_card_id = str(card_id)
        self.state.show_answers = False
        self._broadcast()

    def toggle_answers(self) -> None:
        self.state.show_answers = not self.state.show_answers
        self._broadcast()

    def hide_card(self) -> None:
        self.state.show_card_id = None
        self.state.show_answers = False
        self._broadcast()

    def finish(self) -> None:
        self.state.finished = True
        self._broadcast()

    # ---- pub/sub ---------------------------------------------------------
    def subscribe(self) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def snapshot(self) -> dict:
        return asdict(self.state)

    def _broadcast(self) -> None:
        payload = json.dumps(self.snapshot())
        self._persist_file.write_text(payload)
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:  # pragma: no cover
                pass


async def sse_stream(session: PresenterSession) -> AsyncIterator[str]:
    """Yield SSE-formatted messages until the client disconnects."""
    q = session.subscribe()
    try:
        # Send current state on connect.
        yield f"data: {json.dumps(session.snapshot())}\n\n"
        while True:
            data = await q.get()
            yield f"data: {data}\n\n"
    finally:
        session.unsubscribe(q)


# Process-level session registry (one per event id).
_sessions: dict[str, PresenterSession] = {}


def get_session(event_id: str, persist_dir: Path) -> PresenterSession:
    if event_id not in _sessions:
        _sessions[event_id] = PresenterSession(event_id, persist_dir)
    return _sessions[event_id]


def reset_session(event_id: str) -> None:
    _sessions.pop(event_id, None)
