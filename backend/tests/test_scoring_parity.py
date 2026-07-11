"""Golden parity + unit tests for the scoring engine (PR2 merge gate).

Parity: our engine must reproduce the frozen goldens (produced by executing the
reference ``evaluate_api`` — see ``scripts/gen_goldens.py``) EXACTLY, for the 5
domains and all 30 facets, across all 8 age×sex norm cells.

The golden ``answers_submitted`` are POST-keying values, so they feed the
engine's ``score_prekeyed`` path (bypassing ``apply_keying``), mirroring how the
reference reads already-keyed submitted values.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.scoring.engine import (
    DOMAIN_NAMES,
    apply_keying,
    score,
    score_prekeyed,
)

FIXTURE = Path(__file__).parent / "fixtures" / "golden_scores.json"

# Reference domain LABEL -> our domain letter.
_DOMAIN_LABEL_TO_LETTER = {name.upper(): letter for letter, name in DOMAIN_NAMES.items()}


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _our_scores_by_label(result) -> dict[str, int]:
    """Flatten a ScoreResult into {reference-LABEL: percentile}."""
    out: dict[str, int] = {}
    for letter, ds in result.domains.items():
        out[DOMAIN_NAMES[letter].upper()] = ds.percentile
        for facet in ds.facets:
            out[facet.name] = facet.percentile
    return out


def _fixture_cases():
    return _load_fixture()["cases"]


@pytest.mark.parametrize(
    "case",
    _fixture_cases(),
    ids=[f"{c['sex']}-{c['band']}" for c in _fixture_cases()],
)
def test_parity_all_norm_cells(case):
    """Every domain + facet percentile matches the reference golden exactly."""
    fixture = _load_fixture()
    submitted = fixture["answers_submitted"]
    keyed = {i + 1: submitted[i] for i in range(120)}

    result = score_prekeyed(keyed, age=case["age"], sex=case["sex"])
    ours = _our_scores_by_label(result)
    golden = case["scores"]

    assert set(ours) == set(golden), "label set mismatch"
    mismatches = {k: (ours[k], golden[k]) for k in golden if ours[k] != golden[k]}
    assert not mismatches, f"percentile mismatches (ours, golden): {mismatches}"


def test_parity_covers_all_eight_cells():
    """The fixture exercises every (sex, band) norm cell."""
    cases = _fixture_cases()
    seen = {(c["sex"], c["band"]) for c in cases}
    expected = {
        (sex, band)
        for sex in ("male", "female")
        for band in ("<21", "21-40", "41-60", ">60")
    }
    assert seen == expected


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


def test_keying_reversal():
    """Reverse-keyed items flip on 1..5; positive items pass through."""
    pos = {"keyed": "+"}
    neg = {"keyed": "-"}
    assert [apply_keying(pos, v) for v in range(1, 6)] == [1, 2, 3, 4, 5]
    assert [apply_keying(neg, v) for v in range(1, 6)] == [5, 4, 3, 2, 1]


@pytest.mark.parametrize("bad", [0, 6, -1, 7])
def test_keying_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        apply_keying({"keyed": "+"}, bad)


def test_reverse_keyed_count_is_55():
    """Exactly 55 of the 120 items are negatively keyed."""
    items = json.loads(
        (
            Path(__file__).parents[1]
            / "app"
            / "scoring"
            / "data"
            / "ipip_neo_120.json"
        ).read_text(encoding="utf-8")
    )
    assert len(items) == 120
    assert sum(1 for it in items if it["keyed"] == "-") == 55


@pytest.mark.parametrize(
    "age,expected_band",
    [
        (10, "<21"),
        (20, "<21"),
        (21, "21-40"),  # edge: reference `Age > 20`
        (40, "21-40"),  # edge: reference `Age < 41`
        (41, "41-60"),  # edge: reference `Age > 40`
        (60, "41-60"),  # edge: reference `Age < 61`
        (61, ">60"),  # edge: reference `Age > 60`
        (99, ">60"),
    ],
)
def test_age_band_edges_match_reference(age, expected_band):
    """Band selection matches the reference conditionals at every edge.

    We assert indirectly by comparing the scored result at ``age`` against the
    golden generated at that band's representative age — same band ⇒ identical
    percentiles (norms are constant within a band).
    """
    fixture = _load_fixture()
    submitted = fixture["answers_submitted"]
    keyed = {i + 1: submitted[i] for i in range(120)}

    band_case = next(c for c in fixture["cases"] if c["band"] == expected_band and c["sex"] == "male")
    at_edge = _our_scores_by_label(score_prekeyed(keyed, age=age, sex="male"))
    assert at_edge == band_case["scores"], f"age {age} did not resolve to band {expected_band}"


def test_percentile_clipping_high_and_low():
    """T<32 clips to percentile 1; T>73 clips to 99."""
    # All-1 raw answers (before keying) drive extreme domain raws in both
    # directions across domains, exercising both clips.
    from app.scoring.engine import _percentile

    assert _percentile(20.0) == 1  # far below 32
    assert _percentile(31.999) == 1
    assert _percentile(73.001) == 99
    assert _percentile(90.0) == 99


def test_percentile_midrange_matches_reference_cubic():
    """A mid-range T reproduces the reference cubic value (int-truncated)."""
    from app.scoring.engine import _percentile, CONST1, CONST2, CONST3, CONST4

    t = 50.0
    expected = int(CONST1 - CONST2 * t + CONST3 * t**2 - CONST4 * t**3)
    assert _percentile(t) == expected


def test_score_applies_keying_then_matches_prekeyed():
    """score() (raw path) equals score_prekeyed() on the keyed vector."""
    items = json.loads(
        (
            Path(__file__).parents[1]
            / "app"
            / "scoring"
            / "data"
            / "ipip_neo_120.json"
        ).read_text(encoding="utf-8")
    )
    by_id = {it["id"]: it for it in items}
    raw = {i: ((i * 7) % 5) + 1 for i in range(1, 121)}
    keyed = {i: apply_keying(by_id[i], raw[i]) for i in range(1, 121)}

    a = score(raw, age=28, sex="male").domain_percentiles()
    b = score_prekeyed(keyed, age=28, sex="male").domain_percentiles()
    assert a == b


def test_score_rejects_wrong_answer_count():
    with pytest.raises(ValueError):
        score({1: 3}, age=28, sex="male")


def test_score_rejects_bad_sex():
    raw = {i: 3 for i in range(1, 121)}
    with pytest.raises(ValueError):
        score(raw, age=28, sex="other")


def test_score_result_shape():
    """Result carries 5 domains, each with 6 facets, raw/T/percentile/level."""
    raw = {i: 3 for i in range(1, 121)}
    result = score(raw, age=28, sex="female")
    assert set(result.domains) == {"N", "E", "O", "A", "C"}
    for ds in result.domains.values():
        assert len(ds.facets) == 6
        assert 1 <= ds.percentile <= 99
        assert ds.level in ("low", "average", "high")
        for f in ds.facets:
            assert 1 <= f.percentile <= 99
            assert f.level in ("low", "average", "high")
