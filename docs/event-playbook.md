# Event playbook (T-14d → T-0)

A printable checklist for the two weeks before your event.

## T-14d — Author

- Write `events/<id>/event.yaml`. Decide `win_rule` (`line` is gentlest in a
  1-hour window) and `num_cards`.
- Fill `events/<id>/wordbank.yaml`. Aim for ~3× as many easy entries as
  cells-per-card to keep generation distributions clean.
- Draft `events/<id>/questions.yaml`. The number of questions should be
  ≥ 1.5× the expected median win step from simulation.

## T-7d — Dry run

- `bts cards generate` and `bts simulate --runs 100 --error-rate 0.07`.
  Target: median winner ≤ 25, p10 ≥ 12, P(no winner inside max-questions) < 15%.
  Adjust tier distribution / question count if not.
- Clone the event with `bts event clone --from real-event --to dryrun-real-event`.
- Send dry-run emails to 3-5 willing testers; have them walk the presenter UI.

## T-3d — Freeze

- Final pass on questions + word bank.
- `bts cards generate` (real event) — note the seed in the event yaml.
- `bts cards render --mode both` to produce print + fillable PDFs.
- `bts slides build` to generate the Reveal.js backup deck.

## T-1d — Send

- `bts roster import roster.csv`
- `bts roster assign`
- `bts send --transport graph --dry-run` to verify the log first.
- `bts send --transport graph` for real.
- Spot-check 3 recipients in your inbox.

## T-0 — Run

- `bts serve` on your laptop.
- Open two browser tabs: admin (private) and presenter (public display).
- Run `GET /event/<id>/present/preflight` once before going live.
- Have the Reveal.js HTML deck open in a second window as backup.
- When someone calls bingo: `B` in the presenter tab → enter card ID →
  confirm with the "expected winners" panel before declaring.
