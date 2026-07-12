"""Public form endpoints.

``GET /forms/{form}/items`` serves the item bank the client presents. Crucially
it strips scoring internals (``keyed`` and facet numbers) so the reverse-keying
map never leaks to the browser — the slider emits raw 1..5 and the server keys.
Both forms are backed by a bank: Full = IPIP-NEO-120, Quick = IPIP-NEO-60.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.scoring.engine import _load_items as _load_full_items
from app.scoring.engine_quick import _load_items as _load_quick_items

router = APIRouter()

# Forms we know about; both live.
_KNOWN_FORMS = {"full", "quick"}


def _public_items(items: list[dict]) -> list[dict]:
    """Strip scoring internals from an item bank for the client.

    Exposes only what the client needs to render an item: id, text, and the
    domain letter (harmless, and useful for grouping). ``keyed`` and the facet
    number/name are withheld so the keying map is not derivable client-side.
    """
    return [
        {"id": it["id"], "text": it["text"], "domain": it["domain"]} for it in items
    ]


@lru_cache(maxsize=1)
def _public_full_items() -> list[dict]:
    """The 120 Full-form items with scoring internals removed."""
    return _public_items(_load_full_items())


@lru_cache(maxsize=1)
def _public_quick_items() -> list[dict]:
    """The 60 Quick-form items with scoring internals removed."""
    return _public_items(_load_quick_items())


@router.get("/forms/{form}/items")
async def get_form_items(form: str) -> dict:
    """Return the items for a form.

    * ``full``  -> 120 items without keying/facet internals
    * ``quick`` -> 60 items without keying/facet internals
    * unknown   -> 404
    """
    if form not in _KNOWN_FORMS:
        raise HTTPException(status_code=404, detail=f"unknown form: {form}")

    items = _public_quick_items() if form == "quick" else _public_full_items()
    return {"form": form, "count": len(items), "items": items}
