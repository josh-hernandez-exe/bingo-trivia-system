# Bootstrap a fresh Windows host for running bingo-trivia-system.
$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    winget install --id astral-sh.uv --accept-source-agreements --accept-package-agreements
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}

uv sync
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
uv run bts doctor
