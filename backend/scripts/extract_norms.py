#!/usr/bin/env python3
"""Extract the 8 age x sex norm tables from the reference evaluator.

Provenance script — run once to generate
``backend/app/scoring/data/norms_120.json``. Not imported by the app.

Source: ``/Users/Montrose/IPIP-NEO-PI/app/evaluator.py`` (read-only reference).
The reference stores each norm as a 71-element tuple whose index 0 is a padding
zero and whose indices 1..70 are (see evaluator.py:682-699):

    [1..5]   domain means   (N, E, O, A, C)
    [6..10]  domain SDs     (N, E, O, A, C)
    [11..16] N facet means  [17..22] N facet SDs
    [23..28] E facet means  [29..34] E facet SDs
    [35..40] O facet means  [41..46] O facet SDs
    [47..52] A facet means  [53..58] A facet SDs
    [59..64] C facet means  [65..70] C facet SDs

That is 70 meaningful floats per cell (5 domain means + 5 domain SDs + 30 facet
means + 30 facet SDs = 70). We preserve the padded 71-tuple verbatim so the
scoring engine can index it exactly as the reference does, keeping full float
precision.

Cells are keyed by sex ("male"/"female") and age band. Band boundaries are
copied verbatim from the reference conditionals (evaluator.py:70-680):

    <21      : Age < 21   (reference: ``Age < 21``)
    21-40    : 20 < Age < 41
    41-60    : 40 < Age < 61
    >60      : Age > 60
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

REFERENCE_EVAL = Path("/Users/Montrose/IPIP-NEO-PI/app/evaluator.py")
OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "scoring"
    / "data"
    / "norms_120.json"
)

# (sex, band) in the order they appear in evaluator.py, matched to the exact
# guard expression so we grab the right tuple for each block.
BLOCKS = [
    ("male", "<21", 'Sex == "Male" and Age < 21'),
    ("male", "21-40", 'Sex == "Male" and Age > 20 and Age < 41'),
    ("male", "41-60", 'Sex == "Male" and Age > 40 and Age < 61'),
    ("male", ">60", 'Sex == "Male" and Age > 60'),
    ("female", "<21", 'Sex == "Female" and Age < 21'),
    ("female", "21-40", 'Sex == "Female" and Age > 20 and Age < 41'),
    ("female", "41-60", 'Sex == "Female" and Age > 40 and Age < 61'),
    ("female", ">60", 'Sex == "Female" and Age > 60'),
]


def extract_tuples(source: str) -> dict[str, dict[str, list[float]]]:
    """Parse `norm = ( ... )` assignments guarded by each sex/age condition."""
    tree = ast.parse(source)
    # Find every `if <cond>:` block that assigns `norm = (...)` and record the
    # tuple keyed by the source of its condition.
    by_condition: dict[str, list[float]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        cond_src = ast.unparse(node.test)
        for stmt in node.body:
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "norm"
            ):
                values = ast.literal_eval(stmt.value)
                by_condition[_normalize(cond_src)] = list(values)

    result: dict[str, dict[str, list[float]]] = {"male": {}, "female": {}}
    for sex, band, cond in BLOCKS:
        key = _normalize(cond)
        if key not in by_condition:
            raise SystemExit(f"Norm block not found for: {cond}")
        tup = by_condition[key]
        if len(tup) != 71:
            raise SystemExit(
                f"{sex}/{band}: expected 71-element tuple, got {len(tup)}"
            )
        result[sex][band] = tup
    return result


def _normalize(expr: str) -> str:
    """Collapse whitespace and quote style so guards match ast.unparse output."""
    return (
        re.sub(r"\s+", " ", expr)
        .strip()
        .replace('"', "'")
        .replace("(", "")
        .replace(")", "")
    )


def main() -> None:
    source = REFERENCE_EVAL.read_text(encoding="utf-8")
    norms = extract_tuples(source)

    # Spot-check a couple of known values against evaluator.py.
    assert norms["male"]["<21"][1] == 67.84, norms["male"]["<21"][1]
    assert norms["female"][">60"][70] == 3.66, norms["female"][">60"][70]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(norms, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(len(bands) for bands in norms.values())
    print(f"Wrote {total} norm cells to {OUTPUT}")


if __name__ == "__main__":
    main()
