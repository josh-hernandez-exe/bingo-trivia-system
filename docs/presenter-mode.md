# Presenter mode

The screen-shared view used during the live event.

```bash
uv run bts serve --event my-event
# admin:     http://127.0.0.1:8765/event/my-event
# presenter: http://127.0.0.1:8765/event/my-event/present
```

Open both URLs in different browser tabs. Share **only the presenter tab**
in your call software.

## Keyboard

| Key | Action |
|---|---|
| `Space` / `→` | Next question |
| `←` | Previous question |
| `R` | Reveal answer(s) |
| `P` | Pause / resume timer |
| `T` | +30 seconds |
| `B` | Verify someone's bingo (prompt for card id) |
| `A` | Toggle the card overlay's "show answers" mode |
| `Esc` | Hide overlay |

## Verifying a bingo

When a participant calls bingo:

1. Press `B`. Enter their card id (or email — the input auto-completes).
2. The overlay shows their card with every cell stamped that should be
   stamped by the current question.
3. The admin tab's "expected winners" panel cross-checks: the card id should
   appear in the list if the win is legitimate.

## Restart safety

State is persisted to `events/<id>/runs/presenter-<ts>.json` after every
action. If the browser crashes or you accidentally close the tab, refreshing
restores the exact question, timer, reveal state, and overlay.

## Pre-flight

```bash
curl http://127.0.0.1:8765/event/my-event/present/preflight
```

Reports missing image files and any `answer_ids` not present in the word
bank. Run this before going live.
