"""PDF rendering backends. Public entry point: `get_renderer(name)`."""

from .base import Renderer, RendererProtocol, get_renderer

__all__ = ["Renderer", "RendererProtocol", "get_renderer"]
