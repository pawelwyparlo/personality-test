"""Coach API (all under /api/v1, auth-gated by :func:`require_account`).

Endpoints:
  POST /coach            -> claim a Profile and create its Coach (201)
  GET  /coach            -> the caller's Coach + messages + trait context (200)
  POST /coach/messages   -> persist the user message, then SSE-stream the reply

Identity (ADR-0002): the signed-in Account (Clerk user id) claims exactly one
Profile. Creating a Coach is the claim: it stamps ``clerk_user_id`` on the
Profile. All coach data is keyed by ``profile_id``; Clerk only contributes the
claim + session verification.

Trait context (CONTEXT.md): the Coach always speaks from the Profile's LATEST
completed Test Run — one context, not an archive — so the system prompt and the
"knows: O.. C.." header are rebuilt from that run every time.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sse_starlette.sse import EventSourceResponse

from app.auth.clerk import require_account
from app.coach.prompt import build_system_prompt, trait_context_line
from app.coach.schemas import (
    CoachCreate,
    CoachCreated,
    CoachMessageCreate,
    CoachMessageOut,
    CoachOut,
    TraitContextOut,
)
from app.core.db import get_session, get_session_factory
from app.llm import LLMUnavailable, get_llm_client
from app.models import Coach, CoachMessage, CoachRole, Profile, RunStatus, TestRun

router = APIRouter()

# How many recent turns to feed the model as rolling context.
_HISTORY_WINDOW = 20


async def _latest_completed_run(
    session: AsyncSession, profile_id: uuid.UUID
) -> TestRun | None:
    """The Profile's most recent completed Test Run (its live trait context)."""
    return await session.scalar(
        select(TestRun)
        .where(
            TestRun.profile_id == profile_id,
            TestRun.status == RunStatus.completed,
        )
        .order_by(TestRun.completed_at.desc())
        .limit(1)
    )


async def _coach_for_account(
    session: AsyncSession, account_id: str
) -> Coach | None:
    """The Coach owned by the Profile this Account has claimed, if any."""
    return await session.scalar(
        select(Coach)
        .join(Profile, Coach.profile_id == Profile.id)
        .where(Profile.clerk_user_id == account_id)
    )


@router.post("/coach", status_code=201)
async def create_coach(
    payload: CoachCreate,
    account_id: str = Depends(require_account),
    session: AsyncSession = Depends(get_session),
) -> CoachCreated:
    """Claim ``profile_id`` for the signed-in Account and create its Coach.

    An Account claims exactly one Profile: if it already claimed a *different*
    one, this is a 409. Claiming a Profile someone else owns is a 409. A
    completed Test Run is required (the Coach needs a trait context). A second
    Coach on the same Profile is a 409.
    """
    profile = await session.get(Profile, payload.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not found")

    # This Account may not have claimed a different Profile already.
    other = await session.scalar(
        select(Profile).where(
            Profile.clerk_user_id == account_id,
            Profile.id != payload.profile_id,
        )
    )
    if other is not None:
        raise HTTPException(
            status_code=409, detail="account already has a coached profile"
        )

    # The target Profile may not be claimed by someone else.
    if profile.clerk_user_id is not None and profile.clerk_user_id != account_id:
        raise HTTPException(
            status_code=409, detail="profile is claimed by another account"
        )

    # A Coach needs a trait context: at least one completed Test Run.
    latest = await _latest_completed_run(session, profile.id)
    if latest is None:
        raise HTTPException(
            status_code=409,
            detail="profile has no completed test run to coach from",
        )

    existing = await session.scalar(
        select(Coach).where(Coach.profile_id == profile.id)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="coach already exists")

    # Claim the Profile and create the Coach.
    profile.clerk_user_id = account_id
    coach = Coach(profile_id=profile.id, name="Sol")
    session.add(coach)
    await session.commit()
    await session.refresh(coach)
    return CoachCreated(id=coach.id, name=coach.name)


async def _coach_out(session: AsyncSession, coach: Coach) -> CoachOut:
    latest = await _latest_completed_run(session, coach.profile_id)
    if latest is None or latest.scores is None:
        # A coached Profile always had a completed run; if it somehow lost it,
        # the coach can't render its context.
        raise HTTPException(
            status_code=409, detail="coach has no trait context"
        )
    messages = await session.scalars(
        select(CoachMessage)
        .where(CoachMessage.coach_id == coach.id)
        .order_by(CoachMessage.created_at)
    )
    return CoachOut(
        id=coach.id,
        name=coach.name,
        messages=[
            CoachMessageOut(
                id=m.id, role=m.role, content=m.content, created_at=m.created_at
            )
            for m in messages
        ],
        trait_context=TraitContextOut(
            run_id=latest.id,
            percentiles=trait_context_line(latest.scores),
        ),
    )


@router.get("/coach")
async def get_coach(
    account_id: str = Depends(require_account),
    session: AsyncSession = Depends(get_session),
) -> CoachOut:
    """The caller's Coach with chat history and live trait context; 404 if none."""
    coach = await _coach_for_account(session, account_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="no coach for this account")
    return await _coach_out(session, coach)


@router.post("/coach/messages")
async def post_coach_message(
    payload: CoachMessageCreate,
    account_id: str = Depends(require_account),
    session: AsyncSession = Depends(get_session),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Persist the user message, then SSE-stream Sol's reply token-by-token.

    Keyless LLM: the endpoint returns a non-streamed 503 ``llm_not_configured``
    *before* persisting the user message, so a keyless attempt leaves no orphan
    turn. On success the full assembled reply is persisted as a ``coach`` turn
    after the stream completes.
    """
    coach = await _coach_for_account(session, account_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="no coach for this account")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="message is empty")

    latest = await _latest_completed_run(session, coach.profile_id)
    if latest is None or latest.scores is None:
        raise HTTPException(status_code=409, detail="coach has no trait context")

    # Refuse before persisting anything if no LLM is configured.
    llm = get_llm_client()
    system = build_system_prompt(latest.scores, coach_name=coach.name)
    # Rolling window of prior turns (chronological), then this new user message.
    prior = await session.scalars(
        select(CoachMessage)
        .where(CoachMessage.coach_id == coach.id)
        .order_by(CoachMessage.created_at.desc())
        .limit(_HISTORY_WINDOW)
    )
    window = [
        {"role": m.role.value, "content": m.content}
        for m in reversed(prior.all())
    ]
    window.append({"role": "user", "content": content})

    # Probe the client: a NullClient raises immediately, before any DB write.
    try:
        stream = llm.stream_text(system, window)
        first_iter = stream.__aiter__()
    except LLMUnavailable:
        raise HTTPException(status_code=503, detail="llm_not_configured")

    # Persist the user turn only now that we know we can stream a reply.
    user_msg = CoachMessage(
        coach_id=coach.id, role=CoachRole.user, content=content
    )
    session.add(user_msg)
    await session.commit()

    coach_id = coach.id

    async def event_source():
        # The request session is closed once this handler returns, so the
        # post-stream persist uses a fresh short-lived session from the factory.
        parts: list[str] = []
        try:
            async for chunk in first_iter:
                parts.append(chunk)
                yield {"event": "token", "data": chunk}
        except LLMUnavailable as exc:
            yield {"event": "error", "data": str(exc)}
        finally:
            reply = "".join(parts)
            if reply:
                async with session_factory() as persist_session:
                    persist_session.add(
                        CoachMessage(
                            coach_id=coach_id,
                            role=CoachRole.coach,
                            content=reply,
                        )
                    )
                    await persist_session.commit()
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_source())
