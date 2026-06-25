"""Render slides from `questions.yaml` to Reveal.js HTML or Beamer LaTeX.

Slides exist as a backup deck — the presenter web UI is primary. Same
`questions.yaml` source so they cannot drift.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..models import EventConfig, QuestionSet, WordBank

TEMPLATE_DIR = Path(__file__).parent / "templates"
Backend = Literal["reveal", "beamer"]
Variant = Literal["questions", "answers"]


def _latex_escape(value: object) -> str:
    text = str(value)
    text = text.replace("\\", r"\textbackslash{}")
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("$", r"\$")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    text = text.replace("{", r"\{")
    text = text.replace("}", r"\}")
    text = text.replace("~", r"\textasciitilde{}")
    text = text.replace("^", r"\textasciicircum{}")
    return text


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["tex_backslash"] = "\\"
    env.filters["tex_escape"] = _latex_escape
    return env


def build_slides(
    event: EventConfig,
    questions: QuestionSet,
    wordbank: WordBank,
    out_dir: Path,
    images_dir: Path,
    *,
    backend: Backend = "reveal",
    variant: Variant = "questions",
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    text_for = {e.id: e.text for e in wordbank.entries}
    # Cross-validate.
    missing = [
        (q.index, aid) for q in questions.questions for aid in q.answer_ids if aid not in text_for
    ]
    if missing:
        raise ValueError(f"slide builder: questions reference unknown answer ids: {missing[:5]}")

    enriched = []
    for q in questions.questions:
        enriched.append(
            {
                "index": q.index,
                "prompt": q.prompt,
                "image": q.image,
                "image_caption": q.image_caption,
                "answers": [text_for[a] for a in q.answer_ids],
                "answer_ids": q.answer_ids,
                "speaker_notes": q.speaker_notes,
            }
        )
    if backend == "reveal":
        tpl = _env().get_template("reveal/deck.html.j2")
        html = tpl.render(event=event, questions=enriched, variant=variant)
        out_file = out_dir / f"{variant}.reveal.html"
        out_file.write_text(html)
        # Copy images alongside (referenced as ./images/<file>).
        if images_dir.exists():
            tgt = out_dir / "images"
            tgt.mkdir(exist_ok=True)
            for img in images_dir.rglob("*"):
                if img.is_file():
                    dest = tgt / img.relative_to(images_dir)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(img, dest)
        return out_file
    if backend == "beamer":
        tpl = _env().get_template("beamer/deck.tex.j2")
        tex = tpl.render(event=event, questions=enriched, variant=variant)
        tex_file = out_dir / f"{variant}.beamer.tex"
        tex_file.write_text(tex)
        if shutil.which("tectonic"):
            subprocess.run(["tectonic", "-X", "compile", tex_file.name], cwd=out_dir, check=True)
            pdf = out_dir / f"{variant}.beamer.pdf"
            if pdf.exists():
                return pdf
        return tex_file
    raise ValueError(f"unknown backend {backend!r}")
