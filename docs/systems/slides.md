# slides

`src/bingo_trivia_system/slides/`

Backup deck generation. The presenter web UI is primary; slides exist as a
failure-mode fallback and post-event leave-behind. Same `questions.yaml`
source so they cannot drift from the live game.

## Backends

| Backend | Output | Requirements |
|---|---|---|
| `reveal` (default) | `<variant>.reveal.html` | None — uses Reveal.js from CDN |
| `beamer` | `<variant>.beamer.tex` (→ `.pdf` if `tectonic` is on PATH) | `tectonic` recommended; falls back to leaving the `.tex` file for manual compilation |

## Variants

- `questions` — prompt + image only
- `answers` — prompt + image + revealed answer chips (numbered `N-1`, `N-2`
  for multi-answer groups, matching card stamps)

## Validation

The builder fails if any `questions.yaml` answer id is missing from
`wordbank.yaml`. This catches the most common authoring mistake.
