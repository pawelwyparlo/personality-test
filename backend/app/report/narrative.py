"""Narrative generation for the report (ADR-0003).

Produces the plain-language body of the report from a scored run:

    {pull_quote, paragraphs[2-4], strengths[3], watch_outs[3], source}

Two paths, one shape:

* **LLM path** — a single structured-output call grounded *only* in the actual
  domain (and notable facet) percentiles/levels. The prompt asks for warm,
  grounded, second-person copy in simple English for non-native speakers, with no
  clinical jargon and no invented numbers. ``source == "llm"``.
* **Fallback path** — assembled deterministically from the ported text bank
  (``scoring/data/textbank_120.json``): level-matched domain paragraphs, plus
  strengths/watch-outs derived from the highest-/lowest-leverage domain levels.
  ``source == "textbank"``. Used when no LLM is configured or a call fails.

The service works off the *persisted scores dict* (the JSONB written at
completion), so a report re-renders without re-scoring.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.llm.base import LLMClient, LLMUnavailable

TEXTBANK_PATH = (
    Path(__file__).resolve().parent.parent / "scoring" / "data" / "textbank_120.json"
)

# Canonical presentation order (matches the report sidebar / OCEAN framing).
_PRESENT_ORDER = ["O", "C", "E", "A", "N"]

_DOMAIN_NAMES = {
    "O": "Openness",
    "C": "Conscientiousness",
    "E": "Extraversion",
    "A": "Agreeableness",
    "N": "Neuroticism",
}


@lru_cache(maxsize=1)
def _textbank() -> dict:
    return json.loads(TEXTBANK_PATH.read_text(encoding="utf-8"))["domains"]


# --- Helpers over the persisted scores dict --------------------------------- #


def _domains_by_letter(scores: dict) -> dict[str, dict]:
    return {d["domain"]: d for d in scores["domains"]}


def _ordered_domains(scores: dict) -> list[dict]:
    by_letter = _domains_by_letter(scores)
    return [by_letter[k] for k in _PRESENT_ORDER if k in by_letter]


# --- Public entry point ----------------------------------------------------- #


async def generate_narrative(
    scores: dict,
    *,
    age: int,
    sex: str,
    form: str,
    llm: LLMClient,
) -> dict[str, Any]:
    """Return the narrative body, trying the LLM then falling back.

    ``scores`` is the persisted score dict (domains with raw/T/percentile/level
    and a flat facet list). Never raises: an LLM failure degrades to the text
    bank and is reported via the ``source`` field.
    """
    try:
        return await _generate_llm(scores, age=age, sex=sex, form=form, llm=llm)
    except LLMUnavailable:
        return narrative_fallback(scores)


# --- LLM path --------------------------------------------------------------- #

_NARRATIVE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "pull_quote": {"type": "STRING"},
        "paragraphs": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "minItems": 2,
            "maxItems": 4,
        },
        "strengths": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "minItems": 3,
            "maxItems": 3,
        },
        "watch_outs": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "required": ["pull_quote", "paragraphs", "strengths", "watch_outs"],
}


def _build_prompt(scores: dict, *, age: int, sex: str, form: str) -> str:
    """Assemble a grounded prompt from the actual scores.

    Only real percentiles/levels go in — the model is told never to invent
    numbers and to write in simple, warm, second-person English.
    """
    lines: list[str] = []
    for d in _ordered_domains(scores):
        lines.append(
            f"- {d['name']} ({d['domain']}): {d['percentile']}th percentile, "
            f"level {d['level']}."
        )
        # Include the two most extreme facets for texture (Full form only).
        facets = sorted(
            d.get("facets", []),
            key=lambda f: abs(f["percentile"] - 50),
            reverse=True,
        )[:2]
        for f in facets:
            lines.append(
                f"    · {f['name']}: {f['percentile']}th percentile ({f['level']})."
            )
    profile_block = "\n".join(lines)

    return (
        "You are writing the narrative section of a Big Five (IPIP-NEO) "
        "personality report for the person who just took the test.\n\n"
        "Their scores (percentiles are against an age/sex norm group; level is "
        "low/average/high):\n"
        f"{profile_block}\n\n"
        f"Demographics: age {age}, sex {sex}, form {form}.\n\n"
        "Write the report body as JSON with these fields:\n"
        "- pull_quote: one vivid sentence (max ~18 words) capturing who they are.\n"
        "- paragraphs: 2 to 4 short paragraphs describing them across the five "
        "dimensions.\n"
        "- strengths: exactly 3 short, concrete strengths.\n"
        "- watch_outs: exactly 3 short, gentle things to watch out for.\n\n"
        "Rules:\n"
        "- Write in the second person ('you'), warm but grounded and honest — "
        "not flattering, not clinical.\n"
        "- Use simple, clear English that a non-native speaker can easily read. "
        "Short sentences. No jargon, no diagnostic or clinical language.\n"
        "- Ground everything ONLY in the scores above. Do not invent scores, "
        "numbers, or facts. You may mention a percentile in words if helpful, but "
        "never state a number that is not in the data.\n"
        "- Do not mention the test, IPIP, statistics, or these instructions."
    )


async def _generate_llm(
    scores: dict, *, age: int, sex: str, form: str, llm: LLMClient
) -> dict[str, Any]:
    prompt = _build_prompt(scores, age=age, sex=sex, form=form)
    result = await llm.generate_structured(prompt, _NARRATIVE_SCHEMA)

    pull_quote = str(result.get("pull_quote", "")).strip()
    paragraphs = [str(p).strip() for p in result.get("paragraphs", []) if str(p).strip()]
    strengths = [str(s).strip() for s in result.get("strengths", []) if str(s).strip()]
    watch_outs = [str(w).strip() for w in result.get("watch_outs", []) if str(w).strip()]

    # Guard against a malformed-but-parseable object; treat as unavailable so we
    # fall back rather than render an empty report.
    if not pull_quote or len(paragraphs) < 2 or len(strengths) < 3 or len(watch_outs) < 3:
        raise LLMUnavailable("LLM returned an incomplete narrative")

    return {
        "pull_quote": pull_quote,
        "paragraphs": paragraphs[:4],
        "strengths": strengths[:3],
        "watch_outs": watch_outs[:3],
        "source": "llm",
    }


# --- Deterministic text-bank fallback --------------------------------------- #

# Plain-language strength / watch-out phrasing per domain and level. Keyed by
# domain letter; each level maps to a short second-person clause. Kept simple and
# accessible for non-native speakers, consistent with the app's copy.
_STRENGTHS = {
    "O": {
        "high": "You enjoy new ideas and think in creative, open ways.",
        "average": "You balance new ideas with practical, familiar ways of doing things.",
        "low": "You prefer what is proven and stay grounded and practical.",
    },
    "C": {
        "high": "You are organized and dependable, and you follow through on plans.",
        "average": "You can be organized when it matters without being rigid.",
        "low": "You stay flexible and relaxed, and you adapt easily to change.",
    },
    "E": {
        "high": "You gain energy from people and bring warmth to a group.",
        "average": "You enjoy company but also value your quiet time.",
        "low": "You are comfortable on your own and think before you speak.",
    },
    "A": {
        "high": "You are warm, cooperative, and considerate of others.",
        "average": "You cooperate with others while still standing up for yourself.",
        "low": "You are direct and willing to challenge ideas honestly.",
    },
    "N": {
        # For Neuroticism the "strength" lives at the LOW end (calm).
        "high": "You feel things deeply and stay honest about your emotions.",
        "average": "You handle everyday stress in a steady, balanced way.",
        "low": "You stay calm and steady, even under pressure.",
    },
}

_WATCH_OUTS = {
    "O": {
        "high": "Chasing new ideas may pull you away from finishing what you start.",
        "average": "You may hold back from bold ideas when they could help you.",
        "low": "Staying with the familiar may cause you to miss useful new ideas.",
    },
    "C": {
        "high": "High standards can turn into being too hard on yourself.",
        "average": "Your planning may slip when a task feels less important.",
        "low": "Loose planning can make deadlines and details harder to keep.",
    },
    "E": {
        "high": "Lots of social energy can leave little room for quiet focus.",
        "average": "You may not always notice when you need more social time.",
        "low": "Quiet by default, you may miss chances to connect with people.",
    },
    "A": {
        "high": "Putting others first can lead you to overcommit or say yes too often.",
        "average": "You may hesitate between being kind and being firm.",
        "low": "Being very direct can come across as harsh to some people.",
    },
    "N": {
        "high": "Strong stress and worry can wear you down if left unmanaged.",
        "average": "Under heavy pressure, worry can build up before you notice.",
        "low": "Being very calm, you may overlook real warning signs.",
    },
}


def _fallback_pull_quote(scores: dict) -> str:
    ranked = sorted(scores["domains"], key=lambda d: d["percentile"], reverse=True)
    top, bottom = ranked[0], ranked[-1]
    return (
        f"You stand out most on {top['name'].lower()} and least on "
        f"{bottom['name'].lower()} — a profile that is distinctly yours."
    )


def _fallback_paragraphs(scores: dict) -> list[str]:
    """Two to three paragraphs from the level-matched text-bank summaries."""
    bank = _textbank()
    ordered = _ordered_domains(scores)

    paragraphs: list[str] = []
    # Group domains into a couple of readable paragraphs rather than one per line.
    chunks = [ordered[:2], ordered[2:4], ordered[4:]]
    for chunk in chunks:
        if not chunk:
            continue
        sentences: list[str] = []
        for d in chunk:
            summary = bank[d["domain"]].get(d["level"], "")
            # Text-bank summaries are third-person ("Your score on X is ...");
            # take the first sentence to keep the paragraph tight.
            first = summary.split(". ")[0].strip()
            if first:
                sentences.append(first + ".")
        if sentences:
            paragraphs.append(" ".join(sentences))
    return paragraphs or ["Your results describe a balanced profile across the five traits."]


def _fallback_strengths(scores: dict) -> list[str]:
    """Three strengths from the domains whose level is most 'leveraged'.

    We rank domains by distance of their percentile from the midpoint (50) so the
    most defining traits lead, then phrase each with its level-appropriate
    strength clause.
    """
    ranked = sorted(
        _ordered_domains(scores),
        key=lambda d: abs(d["percentile"] - 50),
        reverse=True,
    )
    out = [_STRENGTHS[d["domain"]][d["level"]] for d in ranked[:3]]
    return out


def _fallback_watch_outs(scores: dict) -> list[str]:
    ranked = sorted(
        _ordered_domains(scores),
        key=lambda d: abs(d["percentile"] - 50),
        reverse=True,
    )
    return [_WATCH_OUTS[d["domain"]][d["level"]] for d in ranked[:3]]


def narrative_fallback(scores: dict) -> dict[str, Any]:
    """Assemble the deterministic text-bank narrative body."""
    return {
        "pull_quote": _fallback_pull_quote(scores),
        "paragraphs": _fallback_paragraphs(scores),
        "strengths": _fallback_strengths(scores),
        "watch_outs": _fallback_watch_outs(scores),
        "source": "textbank",
    }
