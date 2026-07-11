"""Deterministic text-bank narrative — the ADR-0003 fallback.

When no LLM is configured (or a generation call fails), the report still needs a
complete body. This module assembles one deterministically from the ported
reference text bank (``scoring/data/textbank_120.json``) plus a scored
:class:`~app.scoring.engine.ScoreResult`.

The output is a plain data structure (not HTML) so the report layer can render
it however it likes; :func:`narrative_fallback` is pure and side-effect free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.scoring.engine import DOMAIN_ORDER, ScoreResult

TEXTBANK_PATH = (
    Path(__file__).resolve().parent.parent / "scoring" / "data" / "textbank_120.json"
)


@dataclass(frozen=True)
class FacetNarrative:
    name: str
    level: str
    percentile: int
    description: str


@dataclass(frozen=True)
class DomainNarrative:
    domain: str
    name: str
    level: str
    percentile: int
    intro: str
    summary: str  # the low/average/high paragraph for this result's level
    facets: list[FacetNarrative]


@dataclass(frozen=True)
class NarrativeReport:
    """A complete deterministic report body."""

    headline: str
    domains: list[DomainNarrative]
    source: str = "textbank"  # marks this as the fallback, not LLM output


@lru_cache(maxsize=1)
def _load_textbank() -> dict:
    return json.loads(TEXTBANK_PATH.read_text(encoding="utf-8"))["domains"]


def narrative_fallback(score_result: ScoreResult) -> NarrativeReport:
    """Assemble a deterministic narrative report from a scored result.

    For each domain (in canonical N,E,O,A,C order) it selects the level-matched
    summary paragraph and pairs every facet with its ported description and the
    facet's own level/percentile.
    """
    bank = _load_textbank()

    domains: list[DomainNarrative] = []
    for letter in DOMAIN_ORDER:
        ds = score_result.domains[letter]
        entry = bank[letter]

        facets = []
        # Match facet descriptions by name (bank order == within-domain order).
        by_name = {f["name"]: f["description"] for f in entry["facets"]}
        for facet in ds.facets:
            facets.append(
                FacetNarrative(
                    name=facet.name,
                    level=facet.level,
                    percentile=facet.percentile,
                    description=by_name.get(facet.name, ""),
                )
            )

        domains.append(
            DomainNarrative(
                domain=letter,
                name=ds.name,
                level=ds.level,
                percentile=ds.percentile,
                intro=entry["intro"],
                summary=entry[ds.level],
                facets=facets,
            )
        )

    headline = _headline(score_result)
    return NarrativeReport(headline=headline, domains=domains)


def _headline(score_result: ScoreResult) -> str:
    """A short deterministic pull-quote naming the standout domains."""
    ranked = sorted(
        score_result.domains.values(), key=lambda d: d.percentile, reverse=True
    )
    top = ranked[0]
    bottom = ranked[-1]
    return (
        f"Your profile stands out most on {top.name.lower()} "
        f"(around the {top.percentile}th percentile) and least on "
        f"{bottom.name.lower()} (around the {bottom.percentile}th)."
    )
