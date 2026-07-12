"""Quick-form (IPIP-NEO-60) scoring engine — domain-only (ADR-0004).

The Quick form is the Maples-Keller (2019) IPIP-NEO-60: 2 items per facet, all
30 facets. It is scored as its own instrument (not a subset of the 120), sharing
the Full form's keying / T-score / cubic-percentile *machinery* but with its own
60-item bank and its own derived domain norms.

Domain-only, by design: with only 2 items per facet, facet scores are too noisy
to report, so this engine computes and returns **five domain percentiles only** —
it never exposes 2-item facet percentiles (see docs/adr/0004 and
docs/research/ipip-neo-60-norms.md).

Pipeline (mirrors ``engine.py`` for the 120):

1. Keying — raw 1..5 answers; the 23 reverse-keyed items flip (``6 - raw``).
2. Domain raw = sum of that domain's 12 items (6 facets × 2). Range 12..60.
3. T-score ``T = 50 + 10 * (raw - mean) / sd`` against the derived domain norm
   cell (keyed by ``"<Sex>|<AgeBand>"``, same 8 sex×age cells as the 120).
4. Percentile via the SAME reference cubic, ``int()``-truncated and clipped to 1
   below T=32 / 99 above T=73 — reusing ``engine._percentile``.
5. Level via the SAME thresholds — reusing ``engine._level``.

The result reuses the engine's :class:`DomainScore` / :class:`ScoreResult` with
each domain's ``facets`` list left empty, so the serializer and every downstream
consumer (report, narrative, coach, PDF) handle a quick run as "domains present,
facets absent" with no special-casing.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.scoring.engine import (
    DATA_DIR,
    DOMAIN_NAMES,
    DOMAIN_ORDER,
    DomainScore,
    ScoreResult,
    Sex,
    _level,
    _norm_band,
    _percentile,
    apply_keying,
)

ITEMS_PATH = DATA_DIR / "ipip_neo_60.json"
NORMS_PATH = DATA_DIR / "norms_60_domains.json"

# The norm JSON keys sex with a leading capital; the API/model uses lowercase.
_SEX_KEY = {"male": "Male", "female": "Female"}


@lru_cache(maxsize=1)
def _load_items() -> list[dict]:
    return json.loads(ITEMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_norms() -> dict:
    return json.loads(NORMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _items_by_id() -> dict[int, dict]:
    return {it["id"]: it for it in _load_items()}


@lru_cache(maxsize=1)
def _domain_item_ids() -> dict[str, list[int]]:
    """Map domain letter -> the 12 item ids that make up its raw score.

    Derived from the bank by grouping on ``domain`` (no id arithmetic — the 60 is
    not interleaved like the 120), so the mapping stays correct regardless of how
    the bank is ordered on disk.
    """
    groups: dict[str, list[int]] = {d: [] for d in DOMAIN_ORDER}
    for it in _load_items():
        groups[it["domain"]].append(it["id"])
    return groups


def _norm_cell(sex: Sex, age: int) -> dict:
    norms = _load_norms()
    key = f"{_SEX_KEY[sex]}|{_norm_band(age)}"
    try:
        return norms[key]
    except KeyError as exc:  # pragma: no cover - guarded by caller
        raise ValueError(f"no norm cell for {key}") from exc


def _score_keyed(keyed: dict[int, int], age: int, sex: Sex) -> ScoreResult:
    """Score already-keyed answers (1..5 per item id 1..60), domain-only."""
    sex = sex.lower()
    if sex not in ("male", "female"):
        raise ValueError(f"sex must be 'male' or 'female', got {sex!r}")
    if len(keyed) != 60:
        raise ValueError(f"expected 60 answers, got {len(keyed)}")

    cell = _norm_cell(sex, age)
    domain_ids = _domain_item_ids()

    domains: dict[str, DomainScore] = {}
    for domain in DOMAIN_ORDER:
        domain_raw = sum(keyed[i] for i in domain_ids[domain])
        norm = cell[domain]
        d_t = 50 + (10 * (domain_raw - norm["mean"]) / norm["sd"])
        domains[domain] = DomainScore(
            domain=domain,
            name=DOMAIN_NAMES[domain],
            raw=domain_raw,
            t_score=d_t,
            percentile=_percentile(d_t),
            level=_level(d_t),
            facets=[],  # domain-only: 2-item facets are never reported
        )

    return ScoreResult(age=age, sex=sex, domains=domains)


def score(answers: dict[int, int], age: int, sex: Sex) -> ScoreResult:
    """Score a completed Quick run from raw slider answers (item id 1..60 -> 1..5).

    Keying is applied here (reverse-keyed items flipped) before the domain sums.
    Returns a domain-only :class:`ScoreResult` (each domain's ``facets`` empty).
    """
    if len(answers) != 60:
        raise ValueError(f"expected 60 answers, got {len(answers)}")
    items = _items_by_id()
    keyed: dict[int, int] = {}
    for item_id, raw in answers.items():
        item = items.get(item_id)
        if item is None:
            raise ValueError(f"unknown item id: {item_id}")
        keyed[item_id] = apply_keying(item, raw)
    return _score_keyed(keyed, age, sex)
