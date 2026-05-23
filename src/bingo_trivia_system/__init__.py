"""bingo-trivia-system — toolkit for running a 1-hour trivia-bingo event end-to-end."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bingo-trivia-system")
except PackageNotFoundError:  # pragma: no cover - editable install edge case
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
