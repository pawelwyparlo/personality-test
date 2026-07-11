"""Form metadata shared by the API layer.

Keeps knowledge of which Items belong to which Form in the scoring package so
the API never hard-codes item counts or IDs. Quick is not yet backed by a bank
(ADR-0004) — its item set is empty until PR6.
"""

from __future__ import annotations

from functools import lru_cache

from app.scoring.engine import _load_items

FULL = "full"
QUICK = "quick"
KNOWN_FORMS = frozenset({FULL, QUICK})


@lru_cache(maxsize=1)
def full_item_ids() -> frozenset[int]:
    """The set of valid Item IDs for the Full form (1..120)."""
    return frozenset(it["id"] for it in _load_items())


def item_ids(form: str) -> frozenset[int]:
    """Valid Item IDs for ``form``. Quick is empty until its bank lands."""
    if form == FULL:
        return full_item_ids()
    return frozenset()


def item_count(form: str) -> int:
    """Number of Items in ``form``."""
    return len(item_ids(form))
