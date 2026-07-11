"""Public form endpoints.

``GET /forms/{form}/items`` serves the item bank the client presents. Crucially
it strips scoring internals (``keyed`` and facet numbers) so the reverse-keying
map never leaks to the browser — the slider emits raw 1..5 and the server keys.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.scoring.engine import _load_items

router = APIRouter()

# Forms we know about. "full" is live; "quick" is planned (PR6) -> 501.
_KNOWN_FORMS = {"full", "quick"}


@lru_cache(maxsize=1)
def _public_full_items() -> list[dict]:
    """The 120 Full-form items with scoring internals removed.

    Exposes only what the client needs to render an item: id, text, and the
    domain letter (harmless, and useful for grouping). ``keyed`` and the facet
    number/name are withheld so the keying map is not derivable client-side.
    """
    return [
        {"id": it["id"], "text": it["text"], "domain": it["domain"]}
        for it in _load_items()
    ]


@router.get("/forms/{form}/items")
async def get_form_items(form: str) -> dict:
    """Return the items for a form.

    * ``full``  -> 120 items without keying/facet internals
    * ``quick`` -> 501 (coming soon; see docs/adr/0004)
    * unknown   -> 404
    """
    if form not in _KNOWN_FORMS:
        raise HTTPException(status_code=404, detail=f"unknown form: {form}")
    if form == "quick":
        raise HTTPException(status_code=501, detail="Quick form coming soon")

    items = _public_full_items()
    return {"form": form, "count": len(items), "items": items}
