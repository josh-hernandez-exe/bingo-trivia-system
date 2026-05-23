# Architectural decisions

Append-only log. One short entry per non-trivial choice. Reference the entry
in your PR description.

---

## 2026-05-23 · Initial scaffold

The first commit lands a complete-but-minimal version of every system in the
plan (cards / simulate / render / email / webui / slides / CLI / sample event)
so contributors have a working baseline to iterate on.

- **Alternatives considered**: thin "hello world" scaffold + multiple follow-up
  PRs. Rejected because the systems are tightly interdependent (CLI needs
  models, web UI needs cards + simulate, etc.) and an empty scaffold provides
  no signal about whether the design works.
- **Trade-off**: this PR is large. Future PRs should be small focused edits.

## 2026-05-23 · ReportLab as default PDF backend

WeasyPrint produces nicer output, but requires Pango/Cairo system libraries
that are painful to install on Windows. ReportLab is pure-Python and ships
without system deps. WeasyPrint remains available as an opt-in extra
(`uv sync --extra weasyprint`) and is pre-installed in the devcontainer.

## 2026-05-23 · Server-Sent Events over WebSockets

The presenter UI broadcasts state changes from the FastAPI process to the
admin tab and the screen-shared presenter tab. SSE is simpler than WebSockets
(plain HTTP, auto-reconnect built into the browser, no extra deps) and the
traffic is one-way (server → browser), so WebSockets add no value here.

## 2026-05-23 · No Node toolchain at runtime

The web UI is server-rendered Jinja with a sprinkle of vanilla JS / Alpine.
There is no `package.json` at the repo root, no bundler, no `node_modules`.
This keeps the Windows-host install path frictionless. Node is only needed in
the devcontainer for the optional Mermaid CLI and codegraph MCP server.

## 2026-05-23 · `starts_at` instead of `datetime` on `EventConfig`

Originally the field was named `datetime`. Pydantic v2 with PEP 563
annotations re-evaluates the type string `datetime | None`, and the field
name `datetime` shadowed the `datetime.datetime` import — Pydantic then saw
`None | None` and failed. Renamed to `starts_at`; cheap and clearer anyway.
