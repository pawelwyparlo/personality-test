"""Tests for the deterministic text-bank narrative fallback (ADR-0003)."""

from __future__ import annotations

import json
from pathlib import Path

from app.report.textbank import narrative_fallback
from app.scoring.engine import DOMAIN_ORDER, score

TEXTBANK = (
    Path(__file__).parents[1]
    / "app"
    / "scoring"
    / "data"
    / "textbank_120.json"
)


def _neutral_result():
    return score({i: 3 for i in range(1, 121)}, age=28, sex="male")


def test_textbank_has_all_domains_and_facets():
    bank = json.loads(TEXTBANK.read_text(encoding="utf-8"))["domains"]
    assert set(bank) == set(DOMAIN_ORDER)
    for entry in bank.values():
        assert entry["intro"]
        for level in ("low", "average", "high"):
            assert entry[level]
        assert len(entry["facets"]) == 6
        for f in entry["facets"]:
            assert f["name"] and f["description"]
            # The template's "Your level of ..." tail must be stripped.
            assert "flev" not in f["description"]
            assert "Your level of" not in f["description"]


def test_narrative_fallback_is_complete():
    report = narrative_fallback(_neutral_result())
    assert report.source == "textbank"
    assert report.headline
    assert len(report.domains) == 5
    # Canonical N,E,O,A,C order.
    assert [d.domain for d in report.domains] == DOMAIN_ORDER
    for dn in report.domains:
        assert dn.intro and dn.summary
        assert len(dn.facets) == 6
        assert dn.level in ("low", "average", "high")
        for f in dn.facets:
            assert f.description
            assert f.level in ("low", "average", "high")


def test_summary_matches_result_level():
    """The domain summary paragraph corresponds to the scored level."""
    bank = json.loads(TEXTBANK.read_text(encoding="utf-8"))["domains"]
    result = _neutral_result()
    report = narrative_fallback(result)
    for dn in report.domains:
        expected = bank[dn.domain][result.domains[dn.domain].level]
        assert dn.summary == expected


def test_narrative_deterministic():
    r = _neutral_result()
    assert narrative_fallback(r) == narrative_fallback(r)
