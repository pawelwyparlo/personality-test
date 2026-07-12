"""Unit tests for the Quick-form (IPIP-NEO-60) scoring engine.

The Quick engine (``engine_quick``) is domain-only by design (ADR-0004): it
shares the Full engine's keying / T-score / cubic-percentile machinery but loads
the 60-item bank and the derived domain-only norms, and never produces facet
scores. These tests lock down: the item bank shape (60 items, 23 reverse-keyed),
the domain raw = sum-of-12 math, the hand-computed T→percentile spot-check from
the norms derivation report, and that facets are always absent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.scoring.engine import _percentile
from app.scoring.engine_quick import (
    _domain_item_ids,
    _load_norms,
    score,
)

DATA_DIR = Path(__file__).parents[1] / "app" / "scoring" / "data"
ITEMS_PATH = DATA_DIR / "ipip_neo_60.json"


def _items() -> list[dict]:
    return json.loads(ITEMS_PATH.read_text(encoding="utf-8"))


# --- Item bank ------------------------------------------------------------- #


def test_bank_has_60_items_ids_1_to_60():
    items = _items()
    assert len(items) == 60
    assert sorted(it["id"] for it in items) == list(range(1, 61))


def test_reverse_keyed_count_is_23():
    """Exactly 23 of the 60 items are negatively keyed (ADR-0004: not 24).

    The source's prose summary says "24 of 60"; the authoritative per-item
    scoring key and the research doc's item table both enumerate 23. The bank
    uses the verified per-item keying.
    """
    items = _items()
    assert sum(1 for it in items if it["keyed"] == "-") == 23


def test_bank_covers_all_30_facets_two_items_each():
    items = _items()
    # 5 domains, 12 items each.
    by_domain: dict[str, int] = {}
    for it in items:
        by_domain[it["domain"]] = by_domain.get(it["domain"], 0) + 1
    assert by_domain == {"N": 12, "E": 12, "O": 12, "A": 12, "C": 12}
    # Every (domain, facet-number) pair has exactly 2 items.
    pairs: dict[tuple[str, int], int] = {}
    for it in items:
        key = (it["domain"], it["facet"]["number"])
        pairs[key] = pairs.get(key, 0) + 1
    assert len(pairs) == 30
    assert all(count == 2 for count in pairs.values())


def test_bank_item_texts_match_research_doc():
    """Spot-check three item texts verbatim against docs/research/ipip-neo-60.md."""
    by_id = {it["id"]: it for it in _items()}
    assert by_id[1]["text"] == "Worry about things."
    assert by_id[15]["text"] == "Love large parties."
    assert by_id[60]["text"] == "Act without thinking."


# --- Norms ----------------------------------------------------------------- #


def test_norms_have_8_cells_5_domains():
    norms = _load_norms()
    assert len(norms) == 8
    expected_cells = {
        f"{sex}|{band}"
        for sex in ("Male", "Female")
        for band in ("<21", "21-40", "41-60", ">60")
    }
    assert set(norms) == expected_cells
    for cell in norms.values():
        assert set(cell) == {"N", "E", "O", "A", "C"}
        for d in cell.values():
            assert d["sd"] > 0 and 12 <= d["mean"] <= 60


def test_domain_item_ids_are_12_each_and_partition_60():
    groups = _domain_item_ids()
    assert set(groups) == {"N", "E", "O", "A", "C"}
    all_ids: list[int] = []
    for ids in groups.values():
        assert len(ids) == 12
        all_ids.extend(ids)
    assert sorted(all_ids) == list(range(1, 61))


# --- Scoring math ---------------------------------------------------------- #


def test_female_21_40_extraversion_spotcheck():
    """Hand-computed check from docs/research/ipip-neo-60-norms.md §6.4.

    Female 21-40, E raw 39 (mean 43.6847, sd 7.6855) → T = 43.9 → percentile 28.
    We build answers that yield an E domain raw of exactly 39 and read back E.
    """
    # E domain: 12 items. Give each a keyed value so the sum is 39 — but answers
    # are RAW slider values, so we must invert keying per item. Easiest: derive
    # the raw values from the bank so post-keying the E sum is a known total.
    items = {it["id"]: it for it in _items()}
    e_ids = _domain_item_ids()["E"]

    # Target keyed E sum = 39 over 12 items. Use keyed value 3 for 11 items and
    # 6 for the last (3*11 + 6 = 39) is impossible (max keyed is 5); instead use
    # a mix: nine 3s (27) + three 4s (12) = 39.
    keyed_targets = {eid: 3 for eid in e_ids}
    for eid in e_ids[:3]:
        keyed_targets[eid] = 4
    assert sum(keyed_targets.values()) == 39

    # Convert each keyed target back to a raw slider value (invert 6-x for "-").
    answers: dict[int, int] = {}
    for iid, it in items.items():
        if iid in keyed_targets:
            k = keyed_targets[iid]
            answers[iid] = (6 - k) if it["keyed"] == "-" else k
        else:
            answers[iid] = 3  # neutral filler for the other 48 items

    result = score(answers, age=30, sex="female")
    e = result.domains["E"]
    assert e.raw == 39
    assert round(e.t_score, 1) == 43.9
    assert e.percentile == 28


def test_domain_raw_is_sum_of_12_keyed_items():
    """Domain raw equals the sum of that domain's 12 keyed item values."""
    answers = {i: 3 for i in range(1, 61)}  # neutral: keying leaves 3 as 3
    result = score(answers, age=30, sex="male")
    for ds in result.domains.values():
        assert ds.raw == 36  # 12 items * 3


def test_result_is_domain_only_no_facets():
    answers = {i: 3 for i in range(1, 61)}
    result = score(answers, age=28, sex="female")
    assert set(result.domains) == {"N", "E", "O", "A", "C"}
    for ds in result.domains.values():
        assert ds.facets == []
        assert 1 <= ds.percentile <= 99
        assert ds.level in ("low", "average", "high")


def test_percentile_reuses_full_engine_cubic():
    """Quick percentiles come from the same cubic + clipping as the 120 path."""
    answers = {i: 3 for i in range(1, 61)}
    result = score(answers, age=30, sex="male")
    for ds in result.domains.values():
        assert ds.percentile == _percentile(ds.t_score)


def test_score_rejects_wrong_answer_count():
    with pytest.raises(ValueError):
        score({1: 3}, age=30, sex="male")


def test_score_rejects_unknown_item():
    answers = {i: 3 for i in range(1, 61)}
    answers.pop(1)
    answers[999] = 3
    with pytest.raises(ValueError):
        score(answers, age=30, sex="male")


def test_score_rejects_bad_sex():
    answers = {i: 3 for i in range(1, 61)}
    with pytest.raises(ValueError):
        score(answers, age=30, sex="other")
