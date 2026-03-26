"""Student-facing API endpoints."""

import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from auth import get_current_user, CurrentUser
from models.schemas import (
    CoverageResponse,
    SyllabusResponse,
    ReadinessResponse,
    DoubtRequest,
    DigestResponse,
)
from engines.ace.chaos_cleaner import chaos_cleaner
from engines.ace.syllabus_mapper import syllabus_mapper
from engines.lre.doc_doubt import doc_doubt
from engines.ace.lecture_digest import lecture_digest

router = APIRouter()


# ─── Coverage & Syllabus ───────────────────────────────────

@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(user: CurrentUser = Depends(get_current_user)):
    """Get syllabus coverage map for the authenticated student."""
    coverage = await chaos_cleaner.get_coverage(
        user_id=user.user_id,
        institution_id=user.institution_id or "",
    )
    return CoverageResponse(coverage=coverage)


@router.get("/syllabus", response_model=SyllabusResponse | None)
async def get_syllabus(user: CurrentUser = Depends(get_current_user)):
    """Get the parsed syllabus for the student's institution."""
    syllabus = await syllabus_mapper.get_syllabus(
        institution_id=user.institution_id or "",
    )
    if not syllabus:
        return None
    return SyllabusResponse(**syllabus)


# ─── DocDoubt — RAG Chat ───────────────────────────────────

@router.post("/doubt")
async def doubt_chat(body: DoubtRequest, user: CurrentUser = Depends(get_current_user)):
    """Stream a grounded answer to a student's question via SSE.

    Uses DocDoubt to search uploaded notes + faculty courseware,
    then streams the LLM response with inline citations.
    """

    async def event_stream():
        # Send source citations first so the frontend can display them
        sources = await doc_doubt.get_sources(
            question=body.message,
            user_id=user.user_id,
            institution_id=user.institution_id or "",
        )
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

        # Stream the response text
        full_response = ""
        async for chunk in doc_doubt.chat(
            question=body.message,
            user_id=user.user_id,
            institution_id=user.institution_id or "",
            conversation_history=None,
        ):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'text', 'data': chunk})}\n\n"

        # Signal completion
        yield f"data: {json.dumps({'type': 'done', 'data': full_response})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/doubt/history")
async def doubt_history(user: CurrentUser = Depends(get_current_user)):
    """List past DocDoubt conversations for the student.

    Stub — will query Supabase chat_history table.
    """
    # TODO: Query Supabase for user's chat_history where agent='doc_doubt'
    return {"conversations": []}


# ─── LectureDigest ─────────────────────────────────────────

@router.post("/digest/{doc_id}", response_model=DigestResponse)
async def generate_digest(
    doc_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a structured summary for a specific uploaded document.

    Returns key concepts, definitions, formulas, and review questions.
    """
    result = await lecture_digest.digest(
        doc_id=doc_id,
        user_id=user.user_id,
        institution_id=user.institution_id or "",
    )
    return DigestResponse(**result)


# ─── Readiness ─────────────────────────────────────────────

@router.get("/readiness", response_model=ReadinessResponse)
async def get_readiness(user: CurrentUser = Depends(get_current_user)):
    """Get the student's current readiness score.

    Stub implementation — returns zeroed values until enough data
    is accumulated from mocks, study sessions, and uploads.
    """
    # TODO: Pull real data from Supabase once mocks/weak_spots/sessions are built
    return ReadinessResponse(
        score=0.0,
        mock_component=0.0,
        gap_component=0.0,
        consistency_component=0.0,
        coverage_component=0.0,
    )
