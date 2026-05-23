from bingo_trivia_system.cards import generate_cards
from bingo_trivia_system.render import get_renderer


def test_reportlab_renders_pdf(sample_event, sample_wordbank):
    card = generate_cards(sample_event, sample_wordbank)[0]
    pdf = get_renderer("reportlab").render(card, sample_wordbank, sample_event, mode="print")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_reportlab_fillable_mode(sample_event, sample_wordbank):
    card = generate_cards(sample_event, sample_wordbank)[0]
    pdf = get_renderer("reportlab").render(card, sample_wordbank, sample_event, mode="fillable")
    assert pdf.startswith(b"%PDF")
