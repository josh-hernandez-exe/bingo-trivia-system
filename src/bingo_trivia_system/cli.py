"""`bts` CLI — thin Typer wrappers around the sibling modules.

Logic stays out of this file by convention; subcommands should not contain
business logic beyond marshalling args / loading inputs / writing outputs.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

from . import cards as cards_mod
from . import simulate as sim_mod
from . import wordbank as wb_mod
from .config import event_paths, list_events, load_event_config
from .email import get_transport
from .email.base import Attachment
from .email.roster import (
    assign,
    load_assignments,
    load_roster_csv,
    reassign,
    save_assignments,
)
from .models import (
    EventConfig,
    QuestionSet,
    WordBank,
)
from .render import get_renderer
from .slides.render import build_slides

console = Console()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = typer.Typer(no_args_is_help=True, help="bingo-trivia-system CLI")
event_app = typer.Typer(help="Event-folder management.")
cards_app = typer.Typer(help="Card generation + PDF rendering.")
roster_app = typer.Typer(help="Roster import + email-to-card assignment.")
slides_app = typer.Typer(help="Backup slide-deck generation.")
docs_app = typer.Typer(help="Documentation parity checks.")
schemas_app = typer.Typer(help="Export Pydantic JSON schemas for IDE autocomplete.")

app.add_typer(event_app, name="event")
app.add_typer(cards_app, name="cards")
app.add_typer(roster_app, name="roster")
app.add_typer(slides_app, name="slides")
app.add_typer(docs_app, name="docs")
app.add_typer(schemas_app, name="schemas")

EventOpt = Annotated[str | None, typer.Option("--event", "-e", help="Event id (or EVENT_DEFAULT)")]


# ---- event --------------------------------------------------------------
@event_app.command("ls")
def event_ls() -> None:
    for eid in list_events():
        console.print(eid)


@event_app.command("new")
def event_new(event_id: str, title: str = "Untitled Event") -> None:
    paths = event_paths(event_id)
    if paths.event_yaml.exists():
        raise typer.BadParameter(f"event {event_id!r} already exists at {paths.root}")
    paths.ensure_dirs()
    paths.event_yaml.write_text(
        yaml.safe_dump(
            EventConfig(id=event_id, title=title).model_dump(mode="json", exclude_none=True),
            sort_keys=False,
        )
    )
    paths.wordbank_yaml.write_text("entries: []\n")
    paths.questions_yaml.write_text("questions: []\n")
    if not paths.roster_csv.exists():
        paths.roster_csv.write_text("email,display_name\n")
    console.print(f"[green]✓[/] created event scaffold at {paths.root}")


@event_app.command("clone")
def event_clone(from_id: str, to_id: str, reset_cards: bool = True) -> None:
    src = event_paths(from_id).root
    dst = event_paths(to_id).root
    if not src.exists():
        raise typer.BadParameter(f"source event {from_id!r} not found")
    if dst.exists():
        raise typer.BadParameter(f"destination event {to_id!r} already exists")
    shutil.copytree(src, dst)
    if reset_cards:
        for sub in ("cards", "runs", "slides"):
            tgt = dst / sub
            if tgt.exists():
                shutil.rmtree(tgt)
        for f in ("assignments.json",):
            if (dst / f).exists():
                (dst / f).unlink()
    # Rewrite id in event.yaml.
    cfg = yaml.safe_load((dst / "event.yaml").read_text())
    cfg["id"] = to_id
    (dst / "event.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    console.print(f"[green]✓[/] cloned {from_id} → {to_id}")


# ---- cards --------------------------------------------------------------
@cards_app.command("generate")
def cards_generate(
    event: EventOpt = None,
    count: int | None = typer.Option(None, "--count", help="override event.num_cards"),
    seed: int | None = typer.Option(None, "--seed", help="override event.seed"),
) -> None:
    paths = event_paths(event)
    paths.ensure_dirs()
    cfg = load_event_config(paths)
    if count:
        cfg = cfg.model_copy(update={"num_cards": count})
    if seed is not None:
        cfg = cfg.model_copy(update={"seed": seed})
    wordbank = wb_mod.load_wordbank(paths.wordbank_yaml)
    wb_mod.validate_for_cards(
        wordbank, num_cards=cfg.num_cards, tier_targets=cfg.tier_distribution.as_dict()
    )
    cards = cards_mod.generate_cards(cfg, wordbank)
    # Wipe pre-existing card files to keep the directory in sync with the seed.
    for old in paths.cards_dir.glob("*.json"):
        old.unlink()
    cards_mod.write_cards(cards, paths.cards_dir)
    console.print(f"[green]✓[/] generated {len(cards)} cards in {paths.cards_dir}")


@cards_app.command("render")
def cards_render(
    event: EventOpt = None,
    backend: str = typer.Option("reportlab", "--backend"),
    mode: str = typer.Option("both", "--mode", help="print | fillable | both"),
) -> None:
    paths = event_paths(event)
    paths.ensure_dirs()
    cfg = load_event_config(paths)
    wordbank = wb_mod.load_wordbank(paths.wordbank_yaml)
    cards = cards_mod.read_cards(paths.cards_dir)
    renderer = get_renderer(backend)
    modes = ("print", "fillable") if mode == "both" else (mode,)
    for c in cards:
        for m in modes:
            pdf = renderer.render(c, wordbank, cfg, mode=m)  # type: ignore[arg-type]
            out = paths.cards_pdf_dir / f"{c.id}.{m}.pdf"
            out.write_bytes(pdf)
    console.print(f"[green]✓[/] rendered {len(cards) * len(modes)} PDFs to {paths.cards_pdf_dir}")


# ---- simulate -----------------------------------------------------------
@app.command("simulate")
def simulate_cmd(
    event: EventOpt = None,
    error_rate: float = 0.05,
    false_positive_rate: float = 0.0,
    runs: int = 1,
    seed: int = 1,
    max_questions: int | None = None,
) -> None:
    paths = event_paths(event)
    cfg = load_event_config(paths)
    cards = cards_mod.read_cards(paths.cards_dir)
    qs = QuestionSet.model_validate(yaml.safe_load(paths.questions_yaml.read_text())).questions

    table = Table(title=f"simulate: {cfg.id} · rule={cfg.win_rule}")
    for col in ("run", "winners", "first", "median", "p10", "p90"):
        table.add_column(col)
    all_results = []
    for r in range(runs):
        result = sim_mod.simulate_event(
            cards,
            qs,
            win_rule=cfg.win_rule,
            seed=seed + r,
            error_rate=error_rate,
            false_positive_rate=false_positive_rate,
            max_questions=max_questions,
        )
        summary = result.summary()
        all_results.append(summary)
        table.add_row(
            str(r),
            str(summary["winners"]),
            str(summary["first_winner_question"]),
            str(summary["median_winner_question"]),
            str(summary["p10"]),
            str(summary["p90"]),
        )
    console.print(table)
    out = paths.runs_dir / f"sim-{int(time.time())}.json"
    paths.runs_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_results, indent=2))
    console.print(f"[dim]wrote {out}[/]")


# ---- roster -------------------------------------------------------------
@roster_app.command("import")
def roster_import(event: EventOpt = None, path: Path = typer.Argument(...)) -> None:
    paths = event_paths(event)
    shutil.copy2(path, paths.roster_csv)
    console.print(f"[green]✓[/] imported {path} → {paths.roster_csv}")


@roster_app.command("assign")
def roster_assign(event: EventOpt = None) -> None:
    paths = event_paths(event)
    cfg = load_event_config(paths)
    roster = load_roster_csv(paths.roster_csv)
    cards = cards_mod.read_cards(paths.cards_dir)
    existing = load_assignments(paths.assignments_json, cfg.id)
    out = assign(cfg.id, roster, cards, existing)
    save_assignments(out, paths.assignments_json)
    console.print(f"[green]✓[/] {len(out.assignments)} assignments → {paths.assignments_json}")


@roster_app.command("reassign")
def roster_reassign(event: EventOpt = None, email: str = typer.Option(...)) -> None:
    paths = event_paths(event)
    cfg = load_event_config(paths)
    cards = cards_mod.read_cards(paths.cards_dir)
    existing = load_assignments(paths.assignments_json, cfg.id)
    out = reassign(existing, email, cards)
    save_assignments(out, paths.assignments_json)
    console.print(f"[green]✓[/] reassigned {email}")


# ---- send ---------------------------------------------------------------
@app.command("send")
def send(
    event: EventOpt = None,
    transport: str = typer.Option("dry-run", "--transport"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    only: str | None = typer.Option(None, "--only", help="send to only this email"),
    force: bool = typer.Option(False, "--force", help="re-send recipients in latest send log"),
    subject: str = "Your bingo card",
) -> None:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    paths = event_paths(event)
    cfg = load_event_config(paths)
    assignments = load_assignments(paths.assignments_json, cfg.id)
    if not assignments.assignments:
        raise typer.BadParameter("no assignments — run `bts roster assign` first")

    template_dir = Path(__file__).parent / "email" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html"]))
    tpl = env.get_template("invite.html.j2")

    tname = "dry-run" if dry_run else transport
    tx = get_transport(tname)

    # Resume log: skip already-sent unless --force.
    sent_emails: set[str] = set()
    logs = sorted(paths.runs_dir.glob("send-*.jsonl"))
    if logs and not force:
        for line in logs[-1].read_text().splitlines():
            row = json.loads(line)
            if row.get("ok"):
                sent_emails.add(row["to"].lower())

    log_path = paths.runs_dir / f"send-{int(time.time())}.jsonl"
    paths.runs_dir.mkdir(parents=True, exist_ok=True)

    with log_path.open("w") as fh:
        for a in assignments.assignments:
            if only and a.email.lower() != only.lower():
                continue
            if a.email.lower() in sent_emails:
                continue
            atts: list[Attachment] = []
            p = paths.cards_pdf_dir / f"{a.card_id}.fillable.pdf"
            if not p.exists():
                console.print(f"[yellow]missing PDF: {p}[/]")
            else:
                atts.append(Attachment(filename=p.name, content=p.read_bytes()))
            html = tpl.render(event=cfg, card_id=str(a.card_id), display_name=a.display_name)
            result = tx.send(a.email, subject, html, atts)
            fh.write(
                json.dumps(
                    {
                        "to": a.email,
                        "ok": result.ok,
                        "message_id": result.message_id,
                        "error": result.error,
                        "transport": tx.name,
                    }
                )
                + "\n"
            )
            status = "[green]✓[/]" if result.ok else "[red]✗[/]"
            console.print(f"{status} {a.email} via {tx.name}")
    console.print(f"[dim]log: {log_path}[/]")


# ---- serve --------------------------------------------------------------
@app.command("serve")
def serve(event: EventOpt = None, host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    if event:
        os.environ["EVENT_DEFAULT"] = event
    uvicorn.run("bingo_trivia_system.webui.app:app", host=host, port=port, reload=False)


# ---- slides -------------------------------------------------------------
@slides_app.command("build")
def slides_build(
    event: EventOpt = None,
    backend: str = typer.Option("reveal", "--backend"),
    variant: str = typer.Option("both", "--variant"),
) -> None:
    paths = event_paths(event)
    cfg = load_event_config(paths)
    wordbank = wb_mod.load_wordbank(paths.wordbank_yaml)
    qs = QuestionSet.model_validate(yaml.safe_load(paths.questions_yaml.read_text()))
    variants = ("questions", "answers") if variant == "both" else (variant,)
    backends = ("reveal", "beamer") if backend == "both" else (backend,)
    for b in backends:
        for v in variants:
            out = build_slides(
                cfg,
                qs,
                wordbank,
                paths.slides_dir,
                paths.images_dir,
                backend=b,  # type: ignore[arg-type]
                variant=v,  # type: ignore[arg-type]
            )
            console.print(f"[green]✓[/] {b}/{v} → {out}")


# ---- doctor -------------------------------------------------------------
@app.command("doctor")
def doctor() -> None:
    table = Table(title="bts doctor — capability check")
    table.add_column("capability")
    table.add_column("status")
    table.add_column("notes")

    def check(name: str, fn) -> None:
        try:
            note = fn() or ""
            table.add_row(name, "[green]ok[/]", note)
        except Exception as e:
            table.add_row(name, "[red]missing[/]", str(e)[:80])

    check("ReportLab", lambda: __import__("reportlab").__name__)
    check("FastAPI", lambda: __import__("fastapi").__name__)
    check("WeasyPrint", lambda: __import__("weasyprint").__name__ + " (extra installed)")
    check("Graph (msal)", lambda: __import__("msal").__name__ + " (extra installed)")
    check("SES (boto3)", lambda: __import__("boto3").__name__ + " (extra installed)")
    check("tectonic (Beamer)", lambda: shutil.which("tectonic") or _missing("tectonic"))
    check("EVENT_DEFAULT", lambda: os.environ.get("EVENT_DEFAULT") or _missing("env var"))
    console.print(table)


def _missing(what: str) -> str:
    raise RuntimeError(f"not found: {what}")


# ---- docs check ---------------------------------------------------------
@docs_app.command("check")
def docs_check() -> None:
    """Verify every src/ subpackage has a matching docs/systems/<name>.md."""

    src_root = Path(__file__).parent
    docs_root = Path("docs/systems")
    problems: list[str] = []
    for child in src_root.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        expected = docs_root / f"{child.name}.md"
        if not expected.exists():
            problems.append(f"missing {expected} for src/bingo_trivia_system/{child.name}/")
    # Also flat-file modules with non-trivial logic.
    for mod in ("cards.py", "simulate.py", "winrules.py", "wordbank.py"):
        name = Path(mod).stem
        expected = docs_root / f"{name}.md"
        if not expected.exists():
            problems.append(f"missing {expected} for src/bingo_trivia_system/{mod}")
    if problems:
        for p in problems:
            console.print(f"[red]✗[/] {p}")
        raise typer.Exit(1)
    console.print("[green]✓[/] docs ↔ code parity ok")


# ---- schemas export -----------------------------------------------------
@schemas_app.command("export")
def schemas_export(out_dir: Path = Path("schemas")) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs: dict[str, type[BaseModel]] = {
        "event.schema.json": EventConfig,
        "wordbank.schema.json": WordBank,
        "questions.schema.json": QuestionSet,
    }
    for name, model in pairs.items():
        (out_dir / name).write_text(json.dumps(model.model_json_schema(), indent=2))
        console.print(f"[green]✓[/] {out_dir / name}")


if __name__ == "__main__":
    app()
