"""Renderer protocol + backend registry."""

from __future__ import annotations

from typing import Literal, Protocol

from ..models import Card, EventConfig, WordBank

RenderMode = Literal["print", "fillable"]


class RendererProtocol(Protocol):
    """Pluggable PDF backend. Backends MUST be deterministic-ish: the output
    file may vary only in non-semantic ways (timestamps, font subset order)."""

    name: str

    def render(
        self,
        card: Card,
        wordbank: WordBank,
        event: EventConfig,
        *,
        mode: RenderMode = "print",
    ) -> bytes:
        """Render a single card to PDF bytes."""
        ...


# Lazy registry so importing this module doesn't require WeasyPrint installed.
def get_renderer(name: str) -> RendererProtocol:
    name = name.lower()
    if name == "reportlab":
        from .reportlab_backend import ReportLabRenderer

        return ReportLabRenderer()
    if name == "weasyprint":
        from .weasyprint_backend import WeasyPrintRenderer

        return WeasyPrintRenderer()
    raise ValueError(f"unknown renderer {name!r}; expected 'reportlab' or 'weasyprint'")


# Alias for type-hinting in CLI without forcing protocol import.
Renderer = RendererProtocol
