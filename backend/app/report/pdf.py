"""Server-side PDF rendering for the report (WeasyPrint).

A dedicated Jinja HTML template (``templates/report.html``) mirrors the on-screen
report — headline, pull-quote, narrative, strengths/watch-outs, the five
dimension bars as CSS, plain-language descriptors, and a footer crediting
IPIP/Johnson plus the date. Rendering is deterministic and dependency-light: no
external assets, no network, CSS bars only (no chart lib), system fonts.

WeasyPrint's native libraries (Pango/Cairo/GDK-Pixbuf) are installed in the
backend image (see the Dockerfile).
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Presentation order and the hard-requirement plain-language descriptors (copy
# written for non-native speakers; must match the on-screen sidebar).
_DIMENSION_ORDER = ["O", "C", "E", "A", "N"]

DIMENSION_DESCRIPTORS: dict[str, str] = {
    "O": "Curiosity and imagination; enjoying new ideas",
    "C": "Being organized and dependable; planning ahead",
    "E": "Where your energy comes from: people or quiet",
    "A": "Being warm, cooperative, considerate",
    "N": "How strongly you feel stress and worry",
}

_FORM_LABELS = {"full": "Full", "quick": "Quick"}


@lru_cache(maxsize=1)
def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )


def _dimensions(scores: dict) -> list[dict]:
    """Ordered dimension rows (name, percentile, descriptor) for the template."""
    by_letter = {d["domain"]: d for d in scores["domains"]}
    rows = []
    for letter in _DIMENSION_ORDER:
        d = by_letter.get(letter)
        if d is None:
            continue
        rows.append(
            {
                "name": d["name"],
                "percentile": d["percentile"],
                "descriptor": DIMENSION_DESCRIPTORS[letter],
            }
        )
    return rows


def render_report_html(scores: dict, narrative: dict, *, form: str) -> str:
    """Render the report HTML (used by the PDF path and testable on its own)."""
    template = _env().get_template("report.html")
    return template.render(
        narrative=narrative,
        dimensions=_dimensions(scores),
        form_label=_FORM_LABELS.get(form, form.title()),
        date=date.today().isoformat(),
    )


def render_report_pdf(scores: dict, narrative: dict, *, form: str) -> bytes:
    """Render the report to PDF bytes via WeasyPrint."""
    # Imported lazily so the module (and its descriptors) import without the
    # native WeasyPrint stack present — e.g. in unit tests that only render HTML.
    from weasyprint import HTML

    html = render_report_html(scores, narrative, form=form)
    return HTML(string=html).write_pdf()
