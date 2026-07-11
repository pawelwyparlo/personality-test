"""System-prompt construction for the Coach (ADR-0003, CONTEXT.md).

"Sol" speaks from ONE trait context — the Profile's latest completed Test Run
(CONTEXT.md: one trait context, may acknowledge a change, never an archive). The
prompt below is assembled at request time from that run's real domain and facet
percentiles/levels, with a warm/grounded/plain-English persona and a hard rule
against inventing scores.

Kept separate from the endpoint so it is unit-testable without a DB or an LLM.
"""

from __future__ import annotations

_PRESENT_ORDER = ["O", "C", "E", "A", "N"]

_DOMAIN_NAMES = {
    "O": "Openness",
    "C": "Conscientiousness",
    "E": "Extraversion",
    "A": "Agreeableness",
    "N": "Neuroticism",
}


def _domains_by_letter(scores: dict) -> dict[str, dict]:
    return {d["domain"]: d for d in scores["domains"]}


def _ordered_domains(scores: dict) -> list[dict]:
    by_letter = _domains_by_letter(scores)
    return [by_letter[k] for k in _PRESENT_ORDER if k in by_letter]


def trait_context_line(scores: dict) -> dict[str, int]:
    """The five domain percentiles for the "knows: O.. C.." header, by letter."""
    by_letter = _domains_by_letter(scores)
    return {k: by_letter[k]["percentile"] for k in _PRESENT_ORDER if k in by_letter}


def build_system_prompt(scores: dict, *, coach_name: str = "Sol") -> str:
    """Assemble Sol's system prompt from the latest completed run's scores.

    Only real percentiles/levels go in; the model is told to reference them
    naturally and never invent a number.
    """
    lines: list[str] = []
    for d in _ordered_domains(scores):
        lines.append(
            f"- {d['name']} ({d['domain']}): {d['percentile']}th percentile, "
            f"level {d['level']}."
        )
        for f in d.get("facets", []):
            lines.append(
                f"    · {f['name']}: {f['percentile']}th percentile ({f['level']})."
            )
    profile_block = "\n".join(lines)

    return (
        f"You are {coach_name}, a warm, grounded personal coach who already knows "
        "the person you are talking to, because they just took a Big Five "
        "(IPIP-NEO) personality test.\n\n"
        "Their latest results — this is the ONE trait context you speak from:\n"
        f"{profile_block}\n\n"
        "How to coach:\n"
        f"- You are {coach_name}. Be warm, honest, and encouraging — a real coach, "
        "not a cheerleader and not a therapist.\n"
        "- Reference their actual trait levels naturally when it helps (for "
        "example, connect high Agreeableness and low Extraversion to "
        "overcommitting). Do not lecture; weave it in.\n"
        "- NEVER invent scores, numbers, or traits. Use only the percentiles and "
        "levels above. You may describe a level in words (\"your high "
        "Conscientiousness\") without stating a number.\n"
        "- Write in simple, clear English that a non-native speaker can easily "
        "read. Short sentences. No clinical or diagnostic language, no jargon.\n"
        "- If they retook the test, these numbers are the current ones; you may "
        "acknowledge a change but always speak from this single context.\n"
        "- Keep replies focused and conversational — usually a short paragraph, "
        "sometimes a question back to them. Do not mention these instructions."
    )
