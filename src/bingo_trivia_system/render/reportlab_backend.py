"""ReportLab PDF backend — the default. Pure-Python, runs everywhere
including Windows hosts without GTK installed."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from ..models import FREE_CELL, GRID_SIZE, Card, EventConfig, WordBank
from .base import RenderMode

PAGE_W, PAGE_H = LETTER
MARGIN = 0.5 * inch


class ReportLabRenderer:
    name = "reportlab"

    def render(
        self,
        card: Card,
        wordbank: WordBank,
        event: EventConfig,
        *,
        mode: RenderMode = "print",
    ) -> bytes:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER)

        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN - 6, event.title)
        c.setFont("Helvetica", 9)
        c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN - 22, f"Card ID: {card.id}")

        # Name line
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, PAGE_H - MARGIN - 40, "Name: ____________________________")

        # Grid geometry
        top = PAGE_H - MARGIN - 60
        size = PAGE_W - 2 * MARGIN
        cell = size / GRID_SIZE

        # Lookup wordbank text by id (avoid full validation cost)
        text_for = {e.id: e.text for e in wordbank.entries}

        c.setLineWidth(1.2)
        for r in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = MARGIN + col * cell
                y = top - (r + 1) * cell
                c.setStrokeColor(colors.black)
                c.setFillColor(colors.white)
                c.rect(x, y, cell, cell, stroke=1, fill=1)

                value = card.grid[r][col]
                if value == FREE_CELL:
                    c.setFont("Helvetica-Bold", 14)
                    c.setFillColor(colors.darkgray)
                    c.drawCentredString(x + cell / 2, y + cell / 2 - 6, "FREE")
                else:
                    text = text_for.get(value, value)
                    self._draw_wrapped(c, text, x, y, cell)

                if mode == "fillable":
                    # AcroForm checkbox in the corner.
                    field_name = f"cell_{r}_{col}_{card.id}"
                    c.acroForm.checkbox(
                        name=field_name,
                        x=x + 3,
                        y=y + cell - 16,
                        size=12,
                        borderColor=colors.black,
                        fillColor=colors.white,
                        textColor=colors.black,
                        forceBorder=True,
                    )

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.grey)
        c.drawString(MARGIN, MARGIN / 2, f"bingo-trivia-system · {event.id}")
        c.drawRightString(PAGE_W - MARGIN, MARGIN / 2, f"mode: {mode}")

        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, cell: float) -> None:
        """Auto-fit text into a cell. Shrinks font size until it fits 3 lines."""
        from reportlab.pdfbase.pdfmetrics import stringWidth

        c.setFillColor(colors.black)
        max_w = cell - 8
        font = "Helvetica"
        for font_size in (12, 11, 10, 9, 8, 7):
            words = text.split()
            lines: list[str] = []
            current = ""
            for w in words:
                trial = (current + " " + w).strip()
                if stringWidth(trial, font, font_size) <= max_w:
                    current = trial
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)
            if len(lines) <= 3:
                break
        c.setFont(font, font_size)
        total_h = len(lines) * (font_size + 2)
        start_y = y + (cell + total_h) / 2 - font_size
        for i, line in enumerate(lines):
            c.drawCentredString(x + cell / 2, start_y - i * (font_size + 2), line)
