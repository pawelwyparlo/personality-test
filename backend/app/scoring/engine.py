"""Pure scoring engine — a faithful port of the reference IPIP-NEO evaluator.

No I/O, no framework dependencies: it takes answers plus demographics and
returns a :class:`ScoreResult`. The item bank and norm tables are loaded once
from the committed JSON data files (see ``scoring/data``); everything else is
arithmetic copied verbatim from ``/Users/Montrose/IPIP-NEO-PI/app/evaluator.py``
so golden parity holds exactly.

Pipeline (per the reference):

1. Keying — raw 1..5 answers; the 55 negatively keyed items are reversed
   (``6 - raw``). The reference baked this into HTML radio values; our slider
   emits raw positions, so we reverse server-side here.
2. Facet raw = sum of its 4 items; facet ``i`` (1..30) uses items
   ``[i, i+30, i+60, i+90]``.
3. Domain raw = sum of its 6 facets.
4. T-score ``T = 50 + 10 * (raw - mean) / sd`` against the age/sex norm cell.
5. Percentile via the reference cubic, truncated with ``int()`` and clipped to
   1 below T=32 / 99 above T=73.
6. Level: low ``T < 45``, average ``45 <= T <= 55``, high ``T > 55``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ITEMS_PATH = DATA_DIR / "ipip_neo_120.json"
NORMS_PATH = DATA_DIR / "norms_120.json"

Sex = str  # "male" | "female"

# Cubic-approximation constants, verbatim from evaluator.py:703-706.
CONST1 = 210.335958661391
CONST2 = 16.7379362643389
CONST3 = 0.405936512733332
CONST4 = 0.00270624341822222

# Domain order as laid out in the norm tuple's domain slots (1..5 means,
# 6..10 SDs) and in the facet slots. Copied from the reference.
DOMAIN_ORDER = ["N", "E", "O", "A", "C"]

# Human-readable domain names for the report layer.
DOMAIN_NAMES = {
    "N": "Neuroticism",
    "E": "Extraversion",
    "O": "Openness",
    "A": "Agreeableness",
    "C": "Conscientiousness",
}

# Per-domain offsets into the 71-element norm tuple for facet means/SDs.
# Facet i (1..6) mean = norm[i + mean_off], sd = norm[i + sd_off].
# Verbatim from evaluator.py:694-699.
_FACET_NORM_OFFSETS = {
    "N": (10, 16),
    "E": (22, 28),
    "O": (34, 40),
    "A": (46, 52),
    "C": (58, 64),
}

# Domain mean/SD indices in the norm tuple (evaluator.py:682-686).
_DOMAIN_NORM_INDEX = {
    "N": (1, 6),
    "E": (2, 7),
    "O": (3, 8),
    "A": (4, 9),
    "C": (5, 10),
}


@dataclass(frozen=True)
class FacetScore:
    """One facet's scores. ``number`` is the within-domain index 1..6."""

    number: int
    name: str
    raw: int
    t_score: float
    percentile: int
    level: str


@dataclass(frozen=True)
class DomainScore:
    """One domain's scores plus its six facets, in within-domain order."""

    domain: str
    name: str
    raw: int
    t_score: float
    percentile: int
    level: str
    facets: list[FacetScore]


@dataclass(frozen=True)
class ScoreResult:
    """The full result of scoring one completed test run."""

    age: int
    sex: Sex
    domains: dict[str, DomainScore]

    def domain_percentiles(self) -> dict[str, int]:
        """Percentiles keyed by domain letter — handy for tests/reports."""
        return {d: ds.percentile for d, ds in self.domains.items()}


@lru_cache(maxsize=1)
def _load_items() -> list[dict]:
    return json.loads(ITEMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_norms() -> dict:
    return json.loads(NORMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _keyed_by_id() -> dict[int, str]:
    return {it["id"]: it["keyed"] for it in _load_items()}


@lru_cache(maxsize=1)
def _facet_meta() -> dict[int, tuple[str, int, str]]:
    """Map facet index 1..30 -> (domain, within-domain number, facet name)."""
    meta: dict[int, tuple[str, int, str]] = {}
    for it in _load_items():
        facet_index = ((it["id"] - 1) % 30) + 1
        if facet_index not in meta:
            meta[facet_index] = (
                it["domain"],
                it["facet"]["number"],
                it["facet"]["name"],
            )
    return meta


def apply_keying(item: dict, raw_value: int) -> int:
    """Return the keyed value for ``raw_value`` (1..5) under ``item``'s keying.

    Positively keyed items pass through; negatively keyed ("-") items reverse
    on the 1..5 scale (``6 - raw``), matching the reference's baked-in reversal.
    """
    if raw_value < 1 or raw_value > 5:
        raise ValueError(f"raw answer out of range 1..5: {raw_value}")
    return (6 - raw_value) if item["keyed"] == "-" else raw_value


def _norm_band(age: int) -> str:
    """Age-band key, copied edge-for-edge from the reference conditionals.

    Reference guards (evaluator.py:70-680):
        Age < 21               -> "<21"
        Age > 20 and Age < 41  -> "21-40"
        Age > 40 and Age < 61  -> "41-60"
        Age > 60               -> ">60"
    """
    if age < 21:
        return "<21"
    if age < 41:  # 21..40 inclusive
        return "21-40"
    if age < 61:  # 41..60 inclusive
        return "41-60"
    return ">60"


def _percentile(t: float) -> int:
    """Reference cubic percentile with int() truncation and clipping."""
    p = int(CONST1 - (CONST2 * t) + (CONST3 * t**2) - (CONST4 * t**3))
    if t < 32:
        p = 1
    if t > 73:
        p = 99
    return p


def _level(t: float) -> str:
    """Level label: low T<45, average 45<=T<=55, high T>55 (evaluator.py)."""
    if t < 45:
        return "low"
    if t <= 55:
        return "average"
    return "high"


def _score_keyed(keyed: dict[int, int], age: int, sex: Sex) -> ScoreResult:
    """Score already-keyed answers (1..5 per item id 1..120).

    This is the shared core used by both the public ``score`` (which keys the
    raw answers first) and the parity harness (which feeds reference post-keying
    vectors directly, bypassing ``apply_keying``).
    """
    sex = sex.lower()
    if sex not in ("male", "female"):
        raise ValueError(f"sex must be 'male' or 'female', got {sex!r}")
    if len(keyed) != 120:
        raise ValueError(f"expected 120 answers, got {len(keyed)}")

    norms = _load_norms()
    band = _norm_band(age)
    try:
        norm = norms[sex][band]
    except KeyError as exc:  # pragma: no cover - guarded above
        raise ValueError(f"no norm cell for {sex}/{band}") from exc

    # Facet raws: facet i (1..30) = items i, i+30, i+60, i+90.
    facet_raw: dict[int, int] = {}
    for i in range(1, 31):
        facet_raw[i] = keyed[i] + keyed[i + 30] + keyed[i + 60] + keyed[i + 90]

    meta = _facet_meta()

    # Group facet indices by domain, preserving within-domain number order.
    # Facet index -> domain is DOMAIN_ORDER[(i-1) % 5]; within-domain number is
    # (i-1)//5 + 1. So a domain's six facets are i = number*5 offset by domain.
    domains: dict[str, DomainScore] = {}
    for d_pos, domain in enumerate(DOMAIN_ORDER):
        facet_indices = [d_pos + 1 + 5 * (num - 1) for num in range(1, 7)]

        facets: list[FacetScore] = []
        domain_raw = 0
        mean_off, sd_off = _FACET_NORM_OFFSETS[domain]
        for facet_index in facet_indices:
            _, number, name = meta[facet_index]
            raw = facet_raw[facet_index]
            domain_raw += raw
            mean = norm[number + mean_off]
            sd = norm[number + sd_off]
            t = 50 + (10 * (raw - mean) / sd)
            facets.append(
                FacetScore(
                    number=number,
                    name=name,
                    raw=raw,
                    t_score=t,
                    percentile=_percentile(t),
                    level=_level(t),
                )
            )

        mean_idx, sd_idx = _DOMAIN_NORM_INDEX[domain]
        d_mean = norm[mean_idx]
        d_sd = norm[sd_idx]
        d_t = 50 + (10 * (domain_raw - d_mean) / d_sd)
        domains[domain] = DomainScore(
            domain=domain,
            name=DOMAIN_NAMES[domain],
            raw=domain_raw,
            t_score=d_t,
            percentile=_percentile(d_t),
            level=_level(d_t),
            facets=facets,
        )

    return ScoreResult(age=age, sex=sex, domains=domains)


def score(answers: dict[int, int], age: int, sex: Sex) -> ScoreResult:
    """Score a completed test run from raw slider answers.

    ``answers`` maps item id (1..120) to a raw 1..5 slider value. Keying is
    applied here (reverse-keyed items flipped) before the shared scoring core.
    """
    if len(answers) != 120:
        raise ValueError(f"expected 120 answers, got {len(answers)}")
    keyed_map = _keyed_by_id()
    keyed: dict[int, int] = {}
    for item_id, raw in answers.items():
        if item_id not in keyed_map:
            raise ValueError(f"unknown item id: {item_id}")
        keyed[item_id] = apply_keying({"keyed": keyed_map[item_id]}, raw)
    return _score_keyed(keyed, age, sex)


def score_prekeyed(keyed_answers: dict[int, int], age: int, sex: Sex) -> ScoreResult:
    """Score answers that are already post-keying (parity-harness entry point).

    Reference verification vectors store submitted (post-keying) values, so they
    must bypass :func:`apply_keying`. Not used by the app's normal flow.
    """
    return _score_keyed(dict(keyed_answers), age, sex)
