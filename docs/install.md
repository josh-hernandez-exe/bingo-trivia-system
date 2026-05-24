# Install

Pick the path that fits your machine. All three end at the same place: a
working `uv run bts` command.

## Windows host (native)

```powershell
winget install astral-sh.uv
git clone https://github.com/josh-hernandez-exe/bingo-trivia-system
cd bingo-trivia-system
uv sync
copy .env.example .env
```

Skip WeasyPrint unless you've installed GTK manually. ReportLab covers all
the essentials.

## Linux host (VM / bare metal)

```bash
sudo apt-get install -y \
  libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev \
  shared-mime-info fonts-dejavu
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/josh-hernandez-exe/bingo-trivia-system
cd bingo-trivia-system
uv sync --all-extras
cp .env.example .env
```

(`scripts/bootstrap-linux.sh` does the same.)

## Devcontainer / GitHub Codespaces

Open the folder in VS Code → command palette → **Reopen in Container**.
Or click **Create Codespace** on GitHub.

`postCreateCommand` runs `uv sync --all-extras` automatically and
`forwardPorts: [8765]` exposes the presenter UI. In the devcontainer,
post-create also installs CodeGraph and Tectonic so repo indexing and the
Beamer PDF fallback work without manual setup.

## Capability matrix

| Capability | Windows | Linux | Devcontainer |
|---|---|---|---|
| `bts` CLI | ✅ | ✅ | ✅ |
| ReportLab PDF | ✅ | ✅ | ✅ |
| WeasyPrint PDF | ⚠️ GTK | ✅ | ✅ |
| Beamer (`tectonic`) | ✅ single binary | ✅ single binary | ✅ installed on create |
| Microsoft Graph | ✅ | ✅ | ✅ |
| AWS SES | ✅ | ✅ | ✅ |
| `bts serve` | ✅ | ✅ via port-forward | ✅ auto-forwarded |

Run `uv run bts doctor` after install to confirm what's wired up.
