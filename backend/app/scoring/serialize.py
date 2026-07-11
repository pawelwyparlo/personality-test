"""Serialize an engine :class:`ScoreResult` to a plain JSON-able dict.

This is the exact shape persisted to ``test_runs.scores`` (JSONB) and returned
by the complete / get-run endpoints. Keeping it here means the storage shape and
the wire shape are defined in one place, next to the engine it mirrors.
"""

from __future__ import annotations

from app.scoring.engine import ScoreResult


def score_result_to_dict(result: ScoreResult, run_id: str) -> dict:
    """Flatten a ScoreResult into nested domains plus a flat facet list."""
    domains = []
    facets = []
    for domain in result.domains.values():
        domain_facets = []
        for f in domain.facets:
            facet_dict = {
                "domain": domain.domain,
                "number": f.number,
                "name": f.name,
                "raw": f.raw,
                "t_score": f.t_score,
                "percentile": f.percentile,
                "level": f.level,
            }
            domain_facets.append(facet_dict)
            facets.append(facet_dict)
        domains.append(
            {
                "domain": domain.domain,
                "name": domain.name,
                "raw": domain.raw,
                "t_score": domain.t_score,
                "percentile": domain.percentile,
                "level": domain.level,
                "facets": domain_facets,
            }
        )
    return {
        "run_id": run_id,
        "age": result.age,
        "sex": result.sex,
        "domains": domains,
        "facets": facets,
    }
