#!/usr/bin/env python3
"""Extract the 120-item IPIP-NEO bank from the reference HTML form.

Provenance script — run once to generate
``backend/app/scoring/data/ipip_neo_120.json``. Not imported by the app.

Source: ``/Users/Montrose/IPIP-NEO-PI/app/views/shortipipneo.html`` (read-only
reference). For each item it records:

* ``id``     — 1..120, the ``Q{n}`` index in the form
* ``text``   — the verbatim statement ("Worry about things.")
* ``domain`` — one of N/E/O/A/C
* ``facet``  — {"number": 1..6, "name": canonical facet name}
* ``keyed``  — "+" or "-"

Keying detection: the reference bakes reverse-keying into the radio VALUEs. A
positively keyed item's "Very Inaccurate" radio carries VALUE="1" (ascending
1..5); a negatively keyed item's "Very Inaccurate" radio carries VALUE="5"
(descending 5..1). We read the VALUE of the first radio (document order, which
is always the "Very Inaccurate" end) for each item: 5 => "-", 1 => "+".

Item -> facet map (IPIP-NEO-120): facet index f = ((id - 1) % 30) + 1, and the
four items of facet f are [f, f+30, f+60, f+90]. Facet f belongs to domain
["N","E","O","A","C"][(f - 1) % 5] with within-domain number (f - 1)//5 + 1.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

REFERENCE_HTML = Path(
    "/Users/Montrose/IPIP-NEO-PI/app/views/shortipipneo.html"
)
OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "scoring"
    / "data"
    / "ipip_neo_120.json"
)

# Canonical domain -> ordered facet names (within-domain numbers 1..6).
# Ported verbatim from the reference evaluator.py label blocks.
FACET_NAMES: dict[str, list[str]] = {
    "N": [
        "Anxiety",
        "Anger",
        "Depression",
        "Self-Consciousness",
        "Immoderation",
        "Vulnerability",
    ],
    "E": [
        "Friendliness",
        "Gregariousness",
        "Assertiveness",
        "Activity Level",
        "Excitement-Seeking",
        "Cheerfulness",
    ],
    "O": [
        "Imagination",
        "Artistic Interests",
        "Emotionality",
        "Adventurousness",
        "Intellect",
        "Liberalism",
    ],
    "A": [
        "Trust",
        "Morality",
        "Altruism",
        "Cooperation",
        "Modesty",
        "Sympathy",
    ],
    "C": [
        "Self-Efficacy",
        "Orderliness",
        "Dutifulness",
        "Achievement-Striving",
        "Self-Discipline",
        "Cautiousness",
    ],
}

DOMAIN_ORDER = ["N", "E", "O", "A", "C"]


def facet_for(item_id: int) -> tuple[str, int, str]:
    """Return (domain, within-domain facet number 1..6, facet name)."""
    facet_index = ((item_id - 1) % 30) + 1  # 1..30
    domain = DOMAIN_ORDER[(facet_index - 1) % 5]
    number = (facet_index - 1) // 5 + 1
    name = FACET_NAMES[domain][number - 1]
    return domain, number, name


def parse_items(source: str) -> list[dict]:
    """Parse the 120 item rows out of the reference HTML."""
    # Each item occupies one table row: a statement cell followed by five
    # radio inputs named Q{n}. Split the document on the item-number cells so
    # each chunk holds exactly one statement + its radios.
    #
    # Rather than rely on brittle whole-row regexes, locate every radio input
    # with its VALUE and group them by item; separately grab the statement text
    # that immediately precedes each item's first radio.
    radio_re = re.compile(
        r'NAME="Q(\d+)"\s+VALUE="(\d)"', re.IGNORECASE
    )

    # first_value[id] = VALUE of the first radio seen for that item (doc order)
    first_value: dict[int, int] = {}
    first_pos: dict[int, int] = {}
    for m in radio_re.finditer(source):
        item_id = int(m.group(1))
        value = int(m.group(2))
        if item_id not in first_value:
            first_value[item_id] = value
            first_pos[item_id] = m.start()

    if len(first_value) != 120:
        raise SystemExit(
            f"Expected 120 items, found {len(first_value)}"
        )

    # Extract the statement text for each item. The statement lives in the
    # table cell just before the item's first radio. We take the text between
    # the item-number cell ("1.&nbsp;", "10.&nbsp;", ...) and the first radio.
    items: list[dict] = []
    for item_id in range(1, 121):
        radio_start = first_pos[item_id]
        # Look back a bounded window for the statement cell.
        window = source[max(0, radio_start - 600) : radio_start]
        text = _extract_statement(window, item_id)
        keyed = "-" if first_value[item_id] == 5 else "+"
        domain, number, name = facet_for(item_id)
        items.append(
            {
                "id": item_id,
                "text": text,
                "domain": domain,
                "facet": {"number": number, "name": name},
                "keyed": keyed,
            }
        )
    return items


def _extract_statement(window: str, item_id: int) -> str:
    """Pull the statement text out of the HTML window before the radios.

    The statement is the last ``<td>...</td>`` cell before the radio inputs
    that is neither the item-number cell nor an empty layout cell.
    """
    # Grab all <td>...</td> cells in the window.
    cells = re.findall(r"<td[^>]*>(.*?)</td>", window, re.DOTALL | re.IGNORECASE)
    for raw in reversed(cells):
        cleaned = _clean_cell(raw)
        if not cleaned:
            continue
        # Skip the item-number cell ("12." / "12.&nbsp;" -> "12.").
        if re.fullmatch(r"\d+\.?", cleaned):
            continue
        return cleaned
    raise SystemExit(f"No statement text found for Q{item_id}")


def _clean_cell(raw: str) -> str:
    """Strip tags/entities/whitespace from a table cell's inner HTML."""
    # Drop any nested tags (<P>, <BR>, etc.).
    no_tags = re.sub(r"<[^>]+>", " ", raw)
    unescaped = html.unescape(no_tags)
    # Collapse whitespace; drop a leading item number if it shares the cell.
    collapsed = re.sub(r"\s+", " ", unescaped).strip()
    collapsed = re.sub(r"^\d+\.\s*", "", collapsed).strip()
    return collapsed


def main() -> None:
    source = REFERENCE_HTML.read_text(encoding="utf-8", errors="replace")
    items = parse_items(source)

    reversed_count = sum(1 for it in items if it["keyed"] == "-")
    if reversed_count != 55:
        raise SystemExit(
            f"Expected 55 reverse-keyed items, found {reversed_count}"
        )

    # Sanity: every statement is non-empty and ends sensibly.
    for it in items:
        if not it["text"]:
            raise SystemExit(f"Empty statement for item {it['id']}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(items, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(items)} items ({reversed_count} reverse-keyed) to {OUTPUT}")


if __name__ == "__main__":
    main()
