# bingo-trivia-system

> Run a 1-hour trivia-bingo event end-to-end — generate unique cards, email them,
> and run a polished local presenter UI that verifies winners live.

[![CI](https://github.com/josh-hernandez-exe/bingo-trivia-system/actions/workflows/ci.yml/badge.svg)](https://github.com/josh-hernandez-exe/bingo-trivia-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)

## Why

Organising a trivia-bingo event with unique cards per participant usually means a
chaotic mix of Excel sheets, ad-hoc email scripts, and a slide deck that drifts
from the answer key. This repo collapses all of that into **one CLI** (`bts`) and
**one local web UI** so you can focus on writing good questions.

## Quickstart

```bash
# 1. Install uv (https://docs.astral.sh/uv/), then:
uv sync

# 2. Bring up the bundled demo event:
export EVENT_DEFAULT=example-shapes-and-colors
uv run bts cards generate
uv run bts cards render
uv run bts simulate --runs 5

# 3. Run the presenter UI:
uv run bts serve
# open http://127.0.0.1:8765
```

## Features

- Deterministic, tier-weighted **card generation** (5×5 with FREE center, seeded).
- Pluggable **PDF backends** — ReportLab (default, Windows-friendly) and
  WeasyPrint (optional, prettier on Linux).
- **Mass email** via Microsoft Graph or AWS SES; resumable send log; `--only`
  flag for the inevitable "I didn't get my card" message.
- Local **FastAPI presenter UI** — dark theme, keyboard-first, SSE-synced admin
  view with "who should have won by now" live table for false-positive defense.
- **Monte-Carlo simulation** to size your question count before event day.
- **Multi-event isolation** (`events/<id>/...`) so the dry-run and the real
  event share zero state.
- Backup **Reveal.js / Beamer slide deck** generated from the same
  `questions.yaml` — cannot drift from the live game.

## CLI overview

```text
bts event    new | ls | clone
bts cards    generate | render
bts roster   import | assign | reassign
bts simulate
bts send                       # transports: graph, ses, dry-run
bts serve                      # FastAPI on 127.0.0.1:8765
bts slides   build             # backends: reveal, beamer
bts doctor                     # capability check
bts schemas  export            # JSON schemas for YAML autocomplete
bts docs     check             # code ↔ docs parity
```

## Install — three paths

| Environment | Steps |
|---|---|
| **Windows host** | `winget install astral-sh.uv && uv sync` |
| **Linux host** | `./scripts/bootstrap-linux.sh` |
| **Devcontainer / Codespaces** | "Reopen in Container" — `postCreateCommand` runs `uv sync --all-extras` for you |

See [`docs/install.md`](docs/install.md) for the per-environment capability matrix.

## Repository layout

```
src/bingo_trivia_system/   # the package
events/                    # per-event data (real ones are gitignored)
tests/                     # pytest suite
docs/                      # systems reference + topic guides
schemas/                   # JSON schemas for YAML files (regen via `bts schemas export`)
scripts/                   # one-shot dev scripts
```

## Configuration

Copy `.env.example` → `.env` and fill in what you need:

- `EVENT_DEFAULT` — saves typing `--event <id>` everywhere.
- `GRAPH_TENANT_ID` / `GRAPH_CLIENT_ID` — only required for `bts send --transport graph`.
- `AWS_PROFILE` / `AWS_REGION` / `SES_FROM_ADDR` — only required for `bts send --transport ses`.

## Documentation

- [Architecture](docs/architecture.md)
- [Event playbook (T-14d → T-0)](docs/event-playbook.md)
- [Volunteer rehearsal](docs/volunteer-rehearsal.md)
- [Authoring questions](docs/authoring-questions.md)
- [Simulation planning report](docs/simulation-planning-report.md)
- [Email setup](docs/email-setup.md)
- [Presenter mode](docs/presenter-mode.md)
- [Systems reference](docs/systems/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). TL;DR:

```bash
uv sync --all-extras
uv run pre-commit install
uv run poe check   # lint + format-check + types + tests + docs + mcp-sync
```

## License

MIT — see [LICENSE](LICENSE).
