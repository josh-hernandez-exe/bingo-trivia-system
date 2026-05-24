import shutil
from pathlib import Path

import pytest

from bingo_trivia_system.cards import generate_cards
from bingo_trivia_system.render import get_renderer
from bingo_trivia_system.slides.render import build_slides


def test_reportlab_renders_pdf(sample_event, sample_wordbank):
    card = generate_cards(sample_event, sample_wordbank)[0]
    pdf = get_renderer("reportlab").render(card, sample_wordbank, sample_event, mode="print")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_reportlab_fillable_mode(sample_event, sample_wordbank):
    card = generate_cards(sample_event, sample_wordbank)[0]
    pdf = get_renderer("reportlab").render(card, sample_wordbank, sample_event, mode="fillable")
    assert pdf.startswith(b"%PDF")


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
