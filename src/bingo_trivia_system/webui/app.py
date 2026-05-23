"""FastAPI app: admin + presenter surfaces."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..cards import read_cards
from ..config import event_paths, list_events, load_event_config
from ..email.roster import load_assignments
from ..models import FREE_CELL, QuestionSet, WordBank
from ..render import get_renderer
from ..simulate import winners_by_question
from .presenter import get_session, sse_stream

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_app() -> FastAPI:
    app = FastAPI(title="bingo-trivia-system")
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    def _ctx(event_id: str) -> dict:
        paths = event_paths(event_id)
        event = load_event_config(paths)
        wordbank = WordBank.model_validate(yaml.safe_load(paths.wordbank_yaml.read_text()))
        cards = read_cards(paths.cards_dir)
        questions = (
            QuestionSet.model_validate(yaml.safe_load(paths.questions_yaml.read_text())).questions
            if paths.questions_yaml.exists()
            else []
        )
        assignments = load_assignments(paths.assignments_json, event_id)
        return {
            "paths": paths,
            "event": event,
            "wordbank": wordbank,
            "cards": cards,
            "questions": questions,
            "assignments": assignments,
        }

    def _stamps_for_card(card, questions) -> dict[tuple[int, int], str]:
        """Map (row, col) -> stamp label ('5' or '5-1', '5-2' for grouped)."""
        index_by_id: dict[str, list[tuple[int, int]]] = {}
        for r in range(5):
            for c in range(5):
                v = card.grid[r][c]
                if v != FREE_CELL:
                    index_by_id.setdefault(v, []).append((r, c))
        stamps: dict[tuple[int, int], str] = {}
        for q in questions:
            matched_cells: list[tuple[int, int]] = []
            for aid in q.answer_ids:
                for cell in index_by_id.get(aid, []):
                    matched_cells.append(cell)
            if len(matched_cells) == 1:
                stamps[matched_cells[0]] = str(q.index)
            else:
                for i, cell in enumerate(matched_cells, start=1):
                    stamps[cell] = f"{q.index}-{i}"
        return stamps

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "index.html", {"events": list_events()})

    @app.get("/event/{event_id}", response_class=HTMLResponse)
    async def event_home(request: Request, event_id: str) -> HTMLResponse:
        ctx = _ctx(event_id)
        return templates.TemplateResponse(
            request,
            "admin.html",
            {
                "event": ctx["event"],
                "assignments": ctx["assignments"].assignments,
                "card_count": len(ctx["cards"]),
                "question_count": len(ctx["questions"]),
            },
        )

    @app.get("/event/{event_id}/card/{card_id}", response_class=HTMLResponse)
    async def card_view(
        request: Request, event_id: str, card_id: str, show_answers: int = 0
    ) -> HTMLResponse:
        ctx = _ctx(event_id)
        card = next((c for c in ctx["cards"] if str(c.id) == card_id), None)
        if card is None:
            raise HTTPException(404, "card not found")
        text_for = {e.id: e.text for e in ctx["wordbank"].entries}
        rows = []
        for r in range(5):
            row = []
            for c in range(5):
                v = card.grid[r][c]
                row.append({"id": v, "text": "FREE" if v == FREE_CELL else text_for.get(v, v)})
            rows.append(row)
        stamps = _stamps_for_card(card, ctx["questions"]) if show_answers else {}
        return templates.TemplateResponse(
            request,
            "card.html",
            {
                "event": ctx["event"],
                "card": card,
                "rows": rows,
                "stamps": {f"{k[0]},{k[1]}": v for k, v in stamps.items()},
                "show_answers": bool(show_answers),
                "assignment": ctx["assignments"].by_card_id(card.id),
            },
        )

    @app.get("/event/{event_id}/card/{card_id}/pdf")
    async def card_pdf(
        event_id: str, card_id: str, mode: str = "print", backend: str = "reportlab"
    ) -> Response:
        ctx = _ctx(event_id)
        card = next((c for c in ctx["cards"] if str(c.id) == card_id), None)
        if card is None:
            raise HTTPException(404)
        renderer = get_renderer(backend)
        pdf = renderer.render(card, ctx["wordbank"], ctx["event"], mode=mode)  # type: ignore[arg-type]
        return Response(content=pdf, media_type="application/pdf")

    @app.get("/event/{event_id}/search")
    async def search(event_id: str, q: str = "") -> JSONResponse:
        ctx = _ctx(event_id)
        q = q.strip().lower()
        results = []
        for a in ctx["assignments"].assignments:
            if (
                q in a.email.lower()
                or q in str(a.card_id).lower()
                or (a.display_name and q in a.display_name.lower())
            ):
                results.append(
                    {
                        "email": a.email,
                        "card_id": str(a.card_id),
                        "display_name": a.display_name,
                    }
                )
        return JSONResponse(results[:50])

    @app.get("/event/{event_id}/expected-winners")
    async def expected_winners(event_id: str) -> JSONResponse:
        ctx = _ctx(event_id)
        session = get_session(event_id, ctx["paths"].runs_dir)
        upto = session.state.current_q_index
        if upto <= 0 or not ctx["questions"]:
            return JSONResponse({"upto_question": upto, "winners": []})
        winners = winners_by_question(
            ctx["cards"], ctx["questions"], win_rule=ctx["event"].win_rule, upto_question=upto
        )
        assignments = ctx["assignments"]
        out = []
        for card_id, q_idx in winners[:25]:
            a = assignments.by_card_id(card_id)
            out.append(
                {
                    "card_id": str(card_id),
                    "won_at": q_idx,
                    "email": a.email if a else None,
                    "display_name": a.display_name if a else None,
                }
            )
        return JSONResponse({"upto_question": upto, "winners": out})

    @app.get("/event/{event_id}/present", response_class=HTMLResponse)
    async def present(request: Request, event_id: str) -> HTMLResponse:
        ctx = _ctx(event_id)
        session = get_session(event_id, ctx["paths"].runs_dir)
        return templates.TemplateResponse(
            request,
            "presenter.html",
            {
                "event": ctx["event"],
                "questions": ctx["questions"],
                "state": session.snapshot(),
            },
        )

    @app.get("/event/{event_id}/present/stream")
    async def present_stream(event_id: str):
        ctx = _ctx(event_id)
        session = get_session(event_id, ctx["paths"].runs_dir)
        return StreamingResponse(sse_stream(session), media_type="text/event-stream")

    @app.post("/event/{event_id}/present/{action}")
    async def present_action(event_id: str, action: str, body: dict | None = None) -> JSONResponse:
        ctx = _ctx(event_id)
        session = get_session(event_id, ctx["paths"].runs_dir)
        body = body or {}
        if action == "advance":
            session.advance()
        elif action == "back":
            session.back()
        elif action == "reveal":
            session.toggle_reveal()
        elif action == "pause":
            session.pause()
        elif action == "add-time":
            session.add_time(int(body.get("seconds", 30)))
        elif action == "show-card":
            session.show_card(body["card_id"])
        elif action == "toggle-answers":
            session.toggle_answers()
        elif action == "hide-card":
            session.hide_card()
        elif action == "finish":
            session.finish()
        else:
            raise HTTPException(400, f"unknown action {action!r}")
        return JSONResponse(session.snapshot())

    @app.get("/event/{event_id}/present/preflight")
    async def preflight(event_id: str) -> JSONResponse:
        ctx = _ctx(event_id)
        problems: list[str] = []
        wb_ids = {e.id for e in ctx["wordbank"].entries}
        answer_ids: set[str] = set()
        for q in ctx["questions"]:
            for aid in q.answer_ids:
                answer_ids.add(aid)
                if aid not in wb_ids:
                    problems.append(f"Q{q.index}: answer id {aid!r} missing from wordbank")
            if q.image:
                img = ctx["paths"].images_dir / q.image
                if not img.exists():
                    problems.append(f"Q{q.index}: image {q.image!r} missing")
        return JSONResponse(
            {
                "ok": not problems,
                "problems": problems,
                "card_count": len(ctx["cards"]),
                "question_count": len(ctx["questions"]),
            }
        )

    return app


app = create_app()
