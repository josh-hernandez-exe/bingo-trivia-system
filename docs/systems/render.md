# render

`src/bingo_trivia_system/render/`

PDF rendering for bingo cards. Pluggable via `RendererProtocol`.

## Backends

| Backend | Module | When to use |
|---|---|---|
| `reportlab` (default) | `reportlab_backend.py` | Always works; ships with the base install. Recommended on Windows. |
| `weasyprint` | `weasyprint_backend.py` | Prettier output (CSS-styled HTML templates). Requires `uv sync --extra weasyprint` and Pango/Cairo system libs. |

## Modes

- `print` — plain card for paper printing.
- `fillable` — adds an AcroForm checkbox per cell so participants can tick in
  Adobe / Edge without printing.

## Public API

```python
from bingo_trivia_system.render import get_renderer
pdf_bytes = get_renderer("reportlab").render(card, wordbank, event, mode="print")
```

## Adding a backend

1. Create `render/<name>_backend.py` with a class that has `name: str` and
   `render(...) -> bytes`.
2. Register the lazy import in `render/base.py:get_renderer()`.
3. Add a smoke test in `tests/test_render.py`.
4. Update `bts doctor` to detect the backend's optional dependency.
