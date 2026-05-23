# Authoring questions

## Files

- `events/<id>/wordbank.yaml` — every cell candidate.
- `events/<id>/questions.yaml` — ordered question list with answer ids.

## Tier guidance

Cells per card (24, excluding FREE) × tier ratio = cells per tier.
At the default `{easy:.55, medium:.30, hard:.15}`:

- ~13 easy
- ~7 medium
- ~4 hard

A safe word bank floor: 3× cells-per-tier per tier (so generation has
breathing room). The bundled demo has 16 / 10 / 8 — enough for 30 cards.

## Multi-answer questions

Some questions have multiple valid responses (e.g. "two colors of the
rainbow"). List every accepted `id` in the `answer_ids` array:

```yaml
- index: 7
  prompt: "Two colors of the rainbow"
  answer_ids: [red, orange, yellow, green, blue]
```

A card containing two of those answers gets two stamps for question 7,
labelled `7-1` and `7-2`.

## Images

Drop image files in `events/<id>/images/` and reference by filename:

```yaml
- index: 8
  prompt: "Name the shape"
  image: octagon.png
  image_caption: "Common road sign"
  answer_ids: [octagon]
```

## Speaker notes (optional)

`speaker_notes: "Trick: many people will say 'red sign' — that's the colour"`
shows up in Reveal.js presenter notes and Beamer `\note{}`.
