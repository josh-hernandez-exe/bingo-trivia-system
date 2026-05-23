"""FastAPI web UI — admin + presenter surfaces sharing one game state."""

from .app import app, create_app

__all__ = ["app", "create_app"]
