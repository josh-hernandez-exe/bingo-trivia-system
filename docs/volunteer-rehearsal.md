# Volunteer rehearsal

Use this when you want to test the full card-generation, PDF-rendering, assignment,
and email-send path with a small group of willing coworkers before the real event.

The intended flow is:

1. Prepare code and reusable instructions here.
2. Commit and push from the devcontainer.
3. Pull the repo on the work machine.
4. Create private event data and send to volunteers from the work machine.
5. Bring any code/doc fixes back as a patch instead of pushing from the work machine.

## What stays private

Do not commit volunteer names, email addresses, generated PDFs, assignments, or
send logs. The repo already ignores `events/*` except the bundled sample event,
and even the sample event ignores generated outputs.

Good local-only files on the work machine:

- `events/volunteer-shapes-and-colors/roster.csv`
- `events/volunteer-shapes-and-colors/assignments.json`
- `events/volunteer-shapes-and-colors/cards/`
- `events/volunteer-shapes-and-colors/runs/`
- `.env`

Do not replace `events/example-shapes-and-colors/roster.csv` with real volunteer
addresses. That sample roster is tracked. Clone the sample event into a local
ignored event and edit the clone instead.

## Prepare this repo

From the devcontainer:

```bash
uv sync --all-extras
uv run poe check
git status --short
git add .devcontainer/devcontainer.json docs/ README.md
git commit -m "docs: add volunteer rehearsal workflow"
git push origin main
```

If the check is too slow while iterating, at minimum run:

```bash
uv run pytest
uv run ruff check .
uv run bts docs check
```

## Pull-only setup on the work machine

Clone or update the repo. Do not push from this machine.

```bash
git clone https://github.com/josh-hernandez-exe/bingo-trivia-system.git
cd bingo-trivia-system
uv sync --all-extras
uv run bts doctor
```

Create a local rehearsal event from the sample shapes-and-colors event. This uses
the sample word bank and questions while keeping volunteer data out of tracked
files.

```bash
uv run bts event clone example-shapes-and-colors volunteer-shapes-and-colors
export EVENT_DEFAULT=volunteer-shapes-and-colors
```

Edit these local files for the rehearsal:

- `events/volunteer-shapes-and-colors/event.yaml`: set title, start time, `num_cards`,
  and seed. Set `num_cards` to at least the number of volunteers plus a small
  buffer. The sample starts at `num_cards: 30`.
- `events/volunteer-shapes-and-colors/wordbank.yaml`: leave the sample content
  in place for the shapes-and-colors rehearsal.
- `events/volunteer-shapes-and-colors/questions.yaml`: leave the sample content
  in place for the shapes-and-colors rehearsal.
- `events/volunteer-shapes-and-colors/roster.csv`: include only volunteers.

Roster format:

```csv
email,display_name
person.one@company.example,Person One
person.two@company.example,Person Two
```

## Generate and inspect cards

```bash
uv run bts cards generate
uv run bts simulate --runs 100 --error-rate 0.07
uv run bts cards render --mode both
uv run bts roster assign
```

Check the generated PDFs before any email leaves the machine:

```bash
find events/$EVENT_DEFAULT/cards/pdf -maxdepth 1 -type f | sort | head
find events/$EVENT_DEFAULT/cards/pdf -maxdepth 1 -type f | wc -l
```

Expected PDF count is `num_cards * 2` because each card has print and fillable
versions.

## Dry-run the send path

The dry run writes the same send log shape as a real send but never contacts an
email provider.

```bash
uv run bts send --transport ses --dry-run --subject "Volunteer bingo rehearsal"
tail -n 20 events/$EVENT_DEFAULT/runs/send-*.jsonl
```

Confirm every volunteer has an `ok: true` row with transport `dry-run`.

## Send one real email first

The email transport for this path is AWS SES. The CLI command is `ses` because it
sends email through Simple Email Service, not SMS/text messages.

If you are using the devcontainer on the work machine, it mounts the host AWS CLI
configuration from `${HOME}/.aws` into `/home/vscode/.aws` inside the container.
If your work machine uses AWS SSO, refresh the SSO login on the host before
opening or rebuilding the container because the mount is read-only.

Create `.env` or export these variables in the terminal:

```bash
AWS_PROFILE=default        # or the profile with SES permissions
AWS_REGION=us-east-1       # or your SES region
SES_FROM_ADDR=trivia@company.example
```

Check that boto3 can see your AWS identity from inside the container:

```bash
uv run python - <<'PY'
import boto3

print(boto3.client("sts").get_caller_identity()["Arn"])
PY
```

Then send to yourself or one volunteer first:

```bash
uv run bts send --transport ses --only you@company.example --force --subject "Volunteer bingo rehearsal"
```

Check the inbox for:

- subject line
- readable HTML body
- one print PDF attachment
- one fillable PDF attachment
- card id visible in the email and matching the PDF filename

## Send to all volunteers

When the single-recipient check passes:

```bash
uv run bts send --transport ses --force --subject "Volunteer bingo rehearsal"
```

Ask volunteers to reply with:

- whether they received exactly one email
- whether both PDFs opened
- whether the fillable PDF accepted marks/checks
- whether the display name and card id looked right

The send command is resumable. If a later run should skip already-successful
recipients, omit `--force`. If you intentionally want to resend, keep `--force`.

## Run the presenter smoke test

On the work machine:

```bash
uv run bts serve
```

Open `http://127.0.0.1:8765`, search for a volunteer by email or name, open their
card PDF, and walk through one mock bingo call. The server binds only localhost,
so screen-share it rather than exposing it on the network.

## Bring fixes back without pushing from work

Use patches for any changes discovered during the rehearsal.

On the work machine, inspect carefully so private files do not end up in the
patch:

```bash
git status --short
git diff -- . ':(exclude)events/*' ':(exclude).env' > volunteer-rehearsal.patch
```

Move `volunteer-rehearsal.patch` back to the devcontainer machine. Apply and
review it here:

```bash
git apply --check volunteer-rehearsal.patch
git apply volunteer-rehearsal.patch
git status --short
uv run poe check
git add <changed-files>
git commit -m "fix: apply volunteer rehearsal findings"
git push origin main
```

If the work-machine changes include event content that should become part of the
real event, sanitize names, email addresses, generated PDFs, assignments, and run
logs before copying anything into the repo.
