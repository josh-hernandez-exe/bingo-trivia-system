# Contributing

Thanks for your interest! This is a small, opinionated repo. The conventions
below keep it pleasant to work in.

## Dev setup

```bash
uv sync --all-extras
uv run pre-commit install
```

If you're on Windows without GTK and don't need WeasyPrint:

```bash
uv sync                       # no extras → ReportLab only
```

The devcontainer (`.devcontainer/`) gives you everything pre-installed if you'd
rather work in a clean environment — open the folder in VS Code and choose
"Reopen in Container", or click "Create Codespace" on GitHub.

## Day-to-day

```bash
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy src/              # types
uv run poe check              # everything CI runs
```

## Conventional Commits

`type(scope): subject` where:

- `type ∈ {feat, fix, docs, chore, refactor, ci, test}`
- `scope ∈ {cards, render, email, webui, slides, cli, docs, ci, deps}`

PR titles follow the same pattern.

## PR checklist

- [ ] `uv run poe check` green
- [ ] Docs in `docs/systems/<module>.md` updated if the module's behaviour changed
- [ ] Regression test added for every bug fix
- [ ] No real participant emails or names in samples / fixtures
- [ ] DECISIONS.md entry added for any non-trivial architectural choice
