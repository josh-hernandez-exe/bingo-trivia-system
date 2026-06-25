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
| `GET /event/<id>/images/<path>` | Serve event-local question images from `events/<id>/images/` |
| `GET /event/<id>/expected-winners` | Cards that should have won by the current question |
| `GET /event/<id>/present/preflight` | Static validation pass (missing images / orphan answers) |

## Routes (presenter)

| Path | Purpose |
|---|---|
| `GET /event/<id>/present` | The screen-shared view |
| `GET /event/<id>/present/stream` | SSE channel that pushes every state change |
| `POST /event/<id>/present/<action>` | `advance`, `back`, `reveal`, `answer-pass`, `pause`, `add-time`, `show-card`, `toggle-answers`, `hide-card`, `finish` |

The presenter template receives questions as JSON-ready data, not raw Pydantic
models, because the browser initializes its local question list through Jinja's
`tojson` filter. That payload includes display answer text resolved through the
word bank, so reveal chips show attendee-facing answers rather than internal
answer IDs. Question images are served through the event image route and may live
in nested folders under the event's `images/` directory.

## Keyboard

`Space` next · `←` back · `R` reveal current question · `A` answer-pass toggle
with confirmation · `P` pause · `T` +30s · `B` open the in-page bingo card
verifier · `Esc` close verifier / hide overlay. The verifier searches by name,
email, or card ID using the same event lookup endpoint as the admin page. When a
called-card overlay is open, `A` still toggles answer stamps for that card.

The presenter countdown is rendered in the browser from the latest SSE state, so
the display ticks every second between server-side state changes.

## State persistence

Every state change is written to `events/<id>/runs/presenter-<ts>.json` so a
browser refresh or process crash restores the last state.
