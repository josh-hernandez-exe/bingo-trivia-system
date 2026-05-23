"""WeasyPrint PDF backend — optional, prettier, Linux-friendly.

Requires the `weasyprint` extra and system libs (Pango, Cairo, GDK-PixBuf).
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..models import FREE_CELL, Card, EventConfig, WordBank
from .base import RenderMode

TEMPLATE_DIR = Path(__file__).parent / "templates"


class WeasyPrintRenderer:
    name = "weasyprint"

    def __init__(self) -> None:
        try:
            from weasyprint import HTML  # noqa: F401
        except ImportError as e:  # pragma: no cover - exercised only when extra missing
            raise RuntimeError(
                "WeasyPrint backend requires the 'weasyprint' extra "
                "and Pango/Cairo system libraries. "
                "Try: uv sync --extra weasyprint"
            ) from e
        self._env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        card: Card,
        wordbank: WordBank,
        event: EventConfig,
        *,
        mode: RenderMode = "print",
    ) -> bytes:
        from weasyprint import HTML

        text_for = {e.id: e.text for e in wordbank.entries}
        rows = []
        for r in card.grid:
            rows.append([("FREE" if cell == FREE_CELL else text_for.get(cell, cell)) for cell in r])
        html = self._env.get_template("card.html.j2").render(
            event=event, card=card, rows=rows, mode=mode
        )
        return HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
