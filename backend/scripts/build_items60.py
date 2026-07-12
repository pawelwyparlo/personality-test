#!/usr/bin/env python3
"""Build the 60-item IPIP-NEO bank (Maples-Keller 2019) for the Quick form.

Provenance script — run once to generate
``backend/app/scoring/data/ipip_neo_60.json``. Not imported by the app.

Source: the verbatim item list in ``docs/research/ipip-neo-60.md`` §2, itself
reproduced from <https://ipip.ori.org/IPIP-NEO-60ScoringKeys.htm>. Each facet has
exactly two items (2 × 30 facets = 60).

Keying note: the research doc's summary line (and the ADR) say "24 of 60 items
are negatively keyed," but the actual per-item markers — in the doc's own item
table AND on the authoritative ipip.ori.org scoring key — enumerate to exactly
**23** reverse-keyed items (N5×2, N6×2, E2×1, O2×1, O3×1, O4×2, O5×2, O6×1, A2×2,
A4×2, A5×2, C2×1, C3×1, C5×1, C6×2). The "24" is an off-by-one in the source's
prose summary; the per-item keying below is authoritative and is used as-is (we
do not invent a 24th reverse item, which would corrupt a domain's scoring).

Item ids are 1..60 in the research-doc order (grouped domain → facet → the two
items of that facet), so the bank reads N1a, N1b, N2a, N2b, … C6a, C6b. Each
record mirrors the 120 bank's shape:

* ``id``     — 1..60
* ``text``   — the verbatim statement
* ``domain`` — one of N/E/O/A/C
* ``facet``  — {"number": 1..6 within-domain, "name": canonical facet name}
* ``keyed``  — "+" or "-"

Unlike the 120, ids here carry NO scoring convention (the 60 is not interleaved
and is not a subset of the 120). The engine derives each facet's two item ids
from this bank by grouping on (domain, facet number); it never assumes id math.
"""

from __future__ import annotations

import json
from pathlib import Path

OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "scoring"
    / "data"
    / "ipip_neo_60.json"
)

DOMAIN_ORDER = ["N", "E", "O", "A", "C"]

# Canonical domain -> ordered facet names (within-domain numbers 1..6), identical
# to the 120 bank's facet naming.
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

# Verbatim from docs/research/ipip-neo-60.md §2. One (text, keying) pair per row,
# grouped domain -> facet (facet number implied by order: 6 facets per domain,
# 2 items each). Keying "+" positive, "-" reverse-keyed.
ITEMS: dict[str, list[list[tuple[str, str]]]] = {
    "N": [
        [("Worry about things.", "+"), ("Get stressed out easily.", "+")],  # N1 Anxiety
        [("Get angry easily.", "+"), ("Lose my temper.", "+")],  # N2 Anger
        [("Often feel blue.", "+"), ("Dislike myself.", "+")],  # N3 Depression
        [
            ("Find it difficult to approach others.", "+"),
            ("Am easily intimidated.", "+"),
        ],  # N4 Self-Consciousness
        [
            ("Rarely overindulge.", "-"),
            ("Am able to control my cravings.", "-"),
        ],  # N5 Immoderation
        [
            ("Remain calm under pressure.", "-"),
            ("Am calm even in tense situations.", "-"),
        ],  # N6 Vulnerability
    ],
    "E": [
        [
            ("Make friends easily.", "+"),
            ("Act comfortably with others.", "+"),
        ],  # E1 Friendliness
        [("Love large parties.", "+"), ("Avoid crowds.", "-")],  # E2 Gregariousness
        [("Take charge.", "+"), ("Try to lead others.", "+")],  # E3 Assertiveness
        [("Am always busy.", "+"), ("Am always on the go.", "+")],  # E4 Activity Level
        [("Love excitement.", "+"), ("Seek adventure.", "+")],  # E5 Excitement-Seeking
        [("Have a lot of fun.", "+"), ("Love life.", "+")],  # E6 Cheerfulness
    ],
    "O": [
        [
            ("Have a vivid imagination.", "+"),
            ("Love to daydream.", "+"),
        ],  # O1 Imagination
        [
            ("Believe in the importance of art.", "+"),
            ("Do not like art.", "-"),
        ],  # O2 Artistic Interests
        [
            ("Experience my emotions intensely.", "+"),
            ("Am not easily affected by my emotions.", "-"),
        ],  # O3 Emotionality
        [
            ("Prefer to stick with things that I know.", "-"),
            ("Don't like the idea of change.", "-"),
        ],  # O4 Adventurousness
        [
            ("Avoid philosophical discussions.", "-"),
            ("Am not interested in theoretical discussions.", "-"),
        ],  # O5 Intellect
        [
            ("Tend to vote for liberal political candidates.", "+"),
            ("Believe in one true religion.", "-"),
        ],  # O6 Liberalism
    ],
    "A": [
        [
            ("Trust others.", "+"),
            ("Believe that others have good intentions.", "+"),
        ],  # A1 Trust
        [
            ("Cheat to get ahead.", "-"),
            ("Take advantage of others.", "-"),
        ],  # A2 Morality
        [
            ("Love to help others.", "+"),
            ("Am concerned about others.", "+"),
        ],  # A3 Altruism
        [("Insult people.", "-"), ("Get back at others.", "-")],  # A4 Cooperation
        [
            ("Believe that I am better than others.", "-"),
            ("Think highly of myself.", "-"),
        ],  # A5 Modesty
        [
            ("Sympathize with the homeless.", "+"),
            ("Feel sympathy for those who are worse off than myself.", "+"),
        ],  # A6 Sympathy
    ],
    "C": [
        [
            ("Handle tasks smoothly.", "+"),
            ("Know how to get things done.", "+"),
        ],  # C1 Self-Efficacy
        [
            ("Like order.", "+"),
            ("Leave a mess in my room.", "-"),
        ],  # C2 Orderliness
        [
            ("Tell the truth.", "+"),
            ("Break my promises.", "-"),
        ],  # C3 Dutifulness
        [
            ("Work hard.", "+"),
            ("Set high standards for myself and others.", "+"),
        ],  # C4 Achievement-Striving
        [
            ("Carry out my plans.", "+"),
            ("Have difficulty starting tasks.", "-"),
        ],  # C5 Self-Discipline
        [
            ("Make rash decisions.", "-"),
            ("Act without thinking.", "-"),
        ],  # C6 Cautiousness
    ],
}


def build() -> list[dict]:
    items: list[dict] = []
    item_id = 1
    for domain in DOMAIN_ORDER:
        for facet_number, pair in enumerate(ITEMS[domain], start=1):
            name = FACET_NAMES[domain][facet_number - 1]
            for text, keyed in pair:
                items.append(
                    {
                        "id": item_id,
                        "text": text,
                        "domain": domain,
                        "facet": {"number": facet_number, "name": name},
                        "keyed": keyed,
                    }
                )
                item_id += 1
    return items


def main() -> None:
    items = build()
    if len(items) != 60:
        raise SystemExit(f"Expected 60 items, built {len(items)}")

    # 23 reverse-keyed per the authoritative per-item scoring key (see module
    # docstring on why this is 23, not the "24" in the source's prose summary).
    reversed_count = sum(1 for it in items if it["keyed"] == "-")
    if reversed_count != 23:
        raise SystemExit(f"Expected 23 reverse-keyed items, found {reversed_count}")

    # Every domain has exactly 12 items (6 facets × 2); every facet exactly 2.
    for domain in DOMAIN_ORDER:
        dom_items = [it for it in items if it["domain"] == domain]
        if len(dom_items) != 12:
            raise SystemExit(f"{domain} has {len(dom_items)} items, expected 12")
        for number in range(1, 7):
            fac_items = [it for it in dom_items if it["facet"]["number"] == number]
            if len(fac_items) != 2:
                raise SystemExit(
                    f"{domain}{number} has {len(fac_items)} items, expected 2"
                )

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
