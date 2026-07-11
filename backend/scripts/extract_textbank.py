#!/usr/bin/env python3
"""Extract the narrative text bank from the reference results template.

Provenance script — run once to generate
``backend/app/scoring/data/textbank_120.json``. Not imported by the app.

Source: ``/Users/Montrose/IPIP-NEO-PI/app/views/results.html`` (read-only
reference Bottle template). For each of the five domains it records:

* ``intro``   — the domain's descriptive paragraphs (level-independent)
* ``low`` / ``average`` / ``high`` — the paragraph shown at each level, with the
  reference's ``% if S? < LO / <= HI / > HI`` guards mapped to low/average/high
* ``facets``  — per facet: ``name`` and ``description`` (the sentence before the
  ``Your level of ... is {{flev[..]}}.`` tail, which is stripped since our
  report supplies the level separately)

The template lists domains in the order Extraversion, Agreeableness,
Conscientiousness, Neuroticism, Openness; we re-key them by domain letter.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

REFERENCE_HTML = Path("/Users/Montrose/IPIP-NEO-PI/app/views/results.html")
OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "scoring"
    / "data"
    / "textbank_120.json"
)

# Domain <h2> heading -> letter, in template order.
DOMAIN_HEADINGS = [
    ("Extraversion", "E"),
    ("Agreeableness", "A"),
    ("Conscientiousness", "C"),
    ("Neuroticism", "N"),
    ("Openness to Experience", "O"),
]

# The short-variable prefix used in the % if guards for each domain.
DOMAIN_GUARD = {"E": "SE", "A": "SA", "C": "SC", "N": "SN", "O": "SO"}


def _clean(text: str) -> str:
    """Strip tags/entities and collapse whitespace to a single clean string."""
    no_tags = re.sub(r"<[^>]+>", "", text)
    unescaped = html.unescape(no_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def _find_domain_bounds(source: str) -> list[tuple[str, int, int]]:
    """Return (letter, start, end) spans for each domain's <h2> section."""
    spans: list[tuple[str, int]] = []
    for heading, letter in DOMAIN_HEADINGS:
        m = re.search(rf"<h2>\s*{re.escape(heading)}\s*</h2>", source, re.IGNORECASE)
        if not m:
            raise SystemExit(f"domain heading not found: {heading}")
        spans.append((letter, m.start()))
    spans.sort(key=lambda s: s[1])
    bounds = []
    for i, (letter, start) in enumerate(spans):
        end = spans[i + 1][1] if i + 1 < len(spans) else len(source)
        bounds.append((letter, start, end))
    return bounds


def _extract_intro(block: str) -> str:
    """Domain intro = all <p>..</p> before the chart <script> tag."""
    head = block.split("<script", 1)[0]
    paras = re.findall(r"<p>(.*?)</p>", head, re.DOTALL | re.IGNORECASE)
    cleaned = [_clean(p) for p in paras]
    cleaned = [c for c in cleaned if c]
    return "\n\n".join(cleaned)


def _extract_levels(block: str, guard: str) -> dict[str, str]:
    """Pull the low/average/high paragraph for a domain from its % if guards."""
    # Guard patterns, mapped to our level names.
    patterns = {
        "low": rf"% if {guard} < LO:(.*?)% end",
        "average": rf"% if {guard} >= LO and {guard} <= HI:(.*?)% end",
        "high": rf"% if {guard} > HI:(.*?)% end",
    }
    out: dict[str, str] = {}
    for level, pat in patterns.items():
        m = re.search(pat, block, re.DOTALL)
        if not m:
            raise SystemExit(f"level block not found: {guard} {level}")
        paras = re.findall(r"<p>(.*?)</p>", m.group(1), re.DOTALL | re.IGNORECASE)
        out[level] = " ".join(_clean(p) for p in paras).strip()
    return out


def _extract_facets(block: str) -> list[dict]:
    """Pull each facet's name + description sentence from the <li> items."""
    ul = re.search(r"Facets\s*</h3>\s*<ul>(.*?)</ul>", block, re.DOTALL | re.IGNORECASE)
    if not ul:
        raise SystemExit("facet <ul> not found in domain block")
    items = re.findall(r"<li>(.*?)</li>", ul.group(1), re.DOTALL | re.IGNORECASE)
    facets = []
    for raw in items:
        name_m = re.search(r"<I>(.*?)</i>", raw, re.IGNORECASE)
        if not name_m:
            raise SystemExit(f"facet name not found in <li>: {raw[:60]!r}")
        name = _clean(name_m.group(1)).rstrip(".")
        # Body after the "<I>Name</i>." lead-in.
        body = raw[name_m.end():]
        text = _clean(body).lstrip(". ").strip()
        # Drop the trailing "Your level of ... is {{flev[..]}}." sentence.
        text = re.sub(r"Your (?:level of|activity level)[^.]*\{\{flev\[\d+\]\}\}\.\s*$", "", text).strip()
        facets.append({"name": name, "description": text})
    if len(facets) != 6:
        raise SystemExit(f"expected 6 facets, got {len(facets)}")
    return facets


def main() -> None:
    source = REFERENCE_HTML.read_text(encoding="utf-8", errors="replace")
    bounds = _find_domain_bounds(source)

    domains: dict[str, dict] = {}
    for letter, start, end in bounds:
        block = source[start:end]
        domains[letter] = {
            "intro": _extract_intro(block),
            **_extract_levels(block, DOMAIN_GUARD[letter]),
            "facets": _extract_facets(block),
        }

    bank = {
        "provenance": (
            "Ported from IPIP-NEO-PI/app/views/results.html (public-domain text "
            "by Dr. John A. Johnson). Facet 'Your level of ... is {{flev}}' tails "
            "stripped; the report supplies levels."
        ),
        "domains": domains,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    facet_total = sum(len(d["facets"]) for d in domains.values())
    print(f"Wrote {len(domains)} domains, {facet_total} facet descriptions to {OUTPUT}")


if __name__ == "__main__":
    main()
