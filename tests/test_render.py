import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth

from bingo_trivia_system import cli
from bingo_trivia_system.cards import generate_cards
from bingo_trivia_system.config import EventPaths
from bingo_trivia_system.render import get_renderer
from bingo_trivia_system.render.reportlab_backend import ReportLabRenderer
from bingo_trivia_system.slides.render import build_slides


def recording_canvas():
    canvas = SimpleNamespace(font="", font_size=0, lines=[])

    def set_fill_color(_color):
        pass

    def set_font(font, font_size):
        canvas.font = font
        canvas.font_size = font_size

    def draw_centred_string(_x, _y, text):
        canvas.lines.append((canvas.font, canvas.font_size, text))

    canvas.setFillColor = set_fill_color
    canvas.setFont = set_font
    canvas.drawCentredString = draw_centred_string
    return canvas


def test_reportlab_renders_pdf(sample_event, sample_wordbank):
    card = generate_cards(sample_event, sample_wordbank)[0]
    pdf = get_renderer("reportlab").render(card, sample_wordbank, sample_event, mode="print")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_reportlab_fillable_mode(sample_event, sample_wordbank):
    card = generate_cards(sample_event, sample_wordbank)[0]
    pdf = get_renderer("reportlab").render(card, sample_wordbank, sample_event, mode="fillable")
    assert pdf.startswith(b"%PDF")


def test_cards_render_writes_only_fillable_pdfs(
    tmp_path, monkeypatch, sample_event, sample_wordbank
):
    event_root = tmp_path / sample_event.id
    cards_dir = event_root / "cards"
    pdf_dir = cards_dir / "pdf"
    pdf_dir.mkdir(parents=True)

    card = generate_cards(sample_event, sample_wordbank)[0]
    (event_root / "event.yaml").write_text(yaml.safe_dump(sample_event.model_dump(mode="json")))
    (event_root / "wordbank.yaml").write_text(
        yaml.safe_dump(sample_wordbank.model_dump(mode="json"))
    )
    (cards_dir / f"{card.id}.json").write_text(json.dumps(card.model_dump(mode="json")))
    (pdf_dir / f"{card.id}.print.pdf").write_bytes(b"stale print")
    (pdf_dir / "stale.fillable.pdf").write_bytes(b"stale fillable")

    monkeypatch.setattr(
        cli,
        "event_paths",
        lambda event: EventPaths(event_id=sample_event.id, root=event_root),
    )

    cli.cards_render(event=sample_event.id, backend="reportlab")

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    assert pdfs == [pdf_dir / f"{card.id}.fillable.pdf"]
    assert pdfs[0].read_bytes().startswith(b"%PDF")


def test_sample_answers_include_multi_answer_and_multi_word_cases(
    sample_questions, sample_wordbank
):
    answer_ids = {entry.id for entry in sample_wordbank.entries if entry.is_answer}
    multi_answer_questions = [q for q in sample_questions.questions if len(q.answer_ids) > 1]

    assert multi_answer_questions
    assert {aid for q in sample_questions.questions for aid in q.answer_ids} <= answer_ids
    assert any(
        len(sample_wordbank.by_id(aid).text.split()) > 1
        for q in multi_answer_questions
        for aid in q.answer_ids
    )


def test_reportlab_wraps_sample_multi_word_answers(sample_wordbank):
    cell = (8.5 * inch - 2 * 0.5 * inch) / 5
    max_width = cell - 8
    answers = [
        entry.text
        for entry in sample_wordbank.entries
        if entry.is_answer and len(entry.text.split()) > 1
    ]

    assert answers
    wrapped_any_answer = False
    for answer in answers:
        canvas = recording_canvas()
        ReportLabRenderer._draw_wrapped(canvas, answer, 0, 0, cell)
        wrapped_any_answer = wrapped_any_answer or len(canvas.lines) > 1

        assert 1 <= len(canvas.lines) <= 3
        for font, font_size, line in canvas.lines:
            assert stringWidth(line, font, font_size) <= max_width

    assert wrapped_any_answer


@pytest.mark.skipif(not shutil.which("tectonic"), reason="tectonic not installed")
def test_beamer_renders_escaped_title(sample_event, sample_wordbank, sample_questions, tmp_path):
    out_dir = tmp_path / "slides"
    images_dir = Path(__file__).resolve().parents[1] / "events" / sample_event.id / "images"

    pdf = build_slides(
        sample_event,
        sample_questions,
        sample_wordbank,
        out_dir,
        images_dir,
        backend="beamer",
        variant="questions",
    )

    assert pdf.suffix == ".pdf"
    assert pdf.exists()
    tex = (out_dir / "questions.beamer.tex").read_text()
    assert r"\title{Shapes \& Colors Bingo (Demo Event)}" in tex
