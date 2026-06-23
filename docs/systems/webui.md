# webui

`src/bingo_trivia_system/webui/`

FastAPI app with two surfaces sharing one in-process game state:

- **Admin** (`/event/<id>`) — search, card preview, "expected winners by now"
  live table. Your private tab during the event.
- **Presenter** (`/event/<id>/present`) — dark-theme, keyboard-first,
  full-bleed view for screen-sharing in your call software.

Started via `bts serve --event <id>` (or `EVENT_DEFAULT` env var). Binds
`127.0.0.1` only — no authentication, no remote access by design.

## Routes (admin)

| Path | Purpose |
|---|---|
| `GET /` | Event picker |
| `GET /event/<id>` | Admin dashboard |
| `GET /event/<id>/search?q=` | Search by email / name / card-id |
| `GET /event/<id>/card/<card-id>?show_answers=0\|1` | Render card mirror with optional stamps |
| `GET /event/<id>/card/<card-id>/pdf` | Download fillable PDF |
| `GET /event/<id>/expected-winners` | Cards that should have won by the current question |
| `GET /event/<id>/present/preflight` | Static validation pass (missing images / orphan answers) |

## Routes (presenter)

| Path | Purpose |
|---|---|
| `GET /event/<id>/present` | The screen-shared view |
| `GET /event/<id>/present/stream` | SSE channel that pushes every state change |
| `POST /event/<id>/present/<action>` | `advance`, `back`, `reveal`, `pause`, `add-time`, `show-card`, `toggle-answers`, `hide-card`, `finish` |

## Keyboard

`Space` next · `←` back · `R` reveal · `P` pause · `T` +30s · `B` verify bingo
· `A` toggle answers · `Esc` hide overlay.

## State persistence

Every state change is written to `events/<id>/runs/presenter-<ts>.json` so a
browser refresh or process crash restores the last state.
