# render

`src/bingo_trivia_system/render/`

PDF rendering for bingo cards. Pluggable via `RendererProtocol`.

## Backends

| Backend | Module | When to use |
|---|---|---|
| `reportlab` (default) | `reportlab_backend.py` | Always works; ships with the base install. Recommended on Windows. |
| `weasyprint` | `weasyprint_backend.py` | Prettier output (CSS-styled HTML templates). Requires `uv sync --extra weasyprint` and Pango/Cairo system libs. |

## Modes

`bts cards render` writes one `<card-id>.fillable.pdf` per card and clears any
stale generated PDFs in `cards/pdf/` first. Fillable PDFs can be printed, so the
normal event workflow does not generate separate print-only PDFs.

The lower-level renderer API still accepts these modes:

- `fillable` — adds an AcroForm checkbox per cell so participants can tick in
  Adobe / Edge without printing, or print the same file.
- `print` — plain card for ad-hoc renderer previews/tests.

## Public API

```python
from bingo_trivia_system.render import get_renderer
pdf_bytes = get_renderer("reportlab").render(card, wordbank, event, mode="fillable")
```

## Adding a backend

1. Create `render/<name>_backend.py` with a class that has `name: str` and
   `render(...) -> bytes`.
2. Register the lazy import in `render/base.py:get_renderer()`.
3. Add a smoke test in `tests/test_render.py`.
4. Update `bts doctor` to detect the backend's optional dependency.
