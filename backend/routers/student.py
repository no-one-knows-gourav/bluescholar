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
    ForgeResponse,
    QuestionListResponse,
    MockGenerateResponse,
    IngestPaperRequest,
    IngestPaperResponse,
    PatternMinerResponse,
    TutorChatRequest,
    WeakSpotsResponse,
    MockSubmitRequest,
    MockSubmitResponse,
    RevisionGenerateRequest,
    RevisionScheduleResponse,
    RebalanceRequest,
    TodoListResponse,
    UpdateTodoRequest,
)
from engines.ace.chaos_cleaner import chaos_cleaner
from engines.ace.syllabus_mapper import syllabus_mapper
from engines.lre.doc_doubt import doc_doubt
from engines.ace.lecture_digest import lecture_digest
from engines.ace.question_forge import question_forge
from engines.ape.smart_mock import smart_mock
from engines.ace.paper_pattern_miner import paper_pattern_miner
from engines.lre.memory_tutor import memory_tutor
from engines.ape.weak_spotter import weak_spotter
from engines.ape.revision_clock import revision_clock

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


# ─── QuestionForge ─────────────────────────────────────────

@router.post("/forge/{doc_id}", response_model=ForgeResponse)
async def forge_questions(
    doc_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a Bloom's-tagged question bank from an uploaded document.

    Scrolls the document's Qdrant chunks in batches and calls Haiku
    to produce 5 questions per batch spanning all Bloom's levels.
    Questions are persisted to the question_bank table.
    """
    result = await question_forge.forge_from_document(
        doc_id=doc_id,
        user_id=user.user_id,
        institution_id=user.institution_id or "",
    )
    return ForgeResponse(**result)


@router.get("/questions", response_model=QuestionListResponse)
async def list_questions(user: CurrentUser = Depends(get_current_user)):
    """List all questions in the student's question bank.

    Stub — will query Supabase question_bank once SmartMock is built.
    """
    # TODO: SELECT * FROM question_bank WHERE user_id = user.user_id
    return QuestionListResponse(questions=[], total=0)


# ─── SmartMock ─────────────────────────────────────────────

@router.post("/mock/generate", response_model=MockGenerateResponse)
async def generate_mock(user: CurrentUser = Depends(get_current_user)):
    """Generate a personalised mock exam paper for the student.

    Selects questions from the question bank, overweighting weak topics
    (2× probability). Renders a PDF via reportlab, uploads to R2, and
    persists a mock record in Supabase.
    """
    result = await smart_mock.generate(
        user_id=user.user_id,
        institution_id=user.institution_id or "",
    )
    return MockGenerateResponse(**result)


@router.post("/mock/{mock_id}/submit", response_model=MockSubmitResponse)
async def submit_mock(
    mock_id: str,
    body: MockSubmitRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Grade a mock submission and update weak spots.

    (Stub implementation — assumes a separate grading step computes scores,
    then we pass those scores to the WeakSpotter.)
    """
    # STUB: Mocked grading logic
    stub_topic_breakdown = [
        {"topic": "Quantum States", "unit": 1, "score": 4.0, "max_score": 10.0},
        {"topic": "Entanglement", "unit": 2, "score": 9.0, "max_score": 10.0},
    ]

    await weak_spotter.update_from_mock(user.user_id, stub_topic_breakdown)

    return MockSubmitResponse(
        score=13.0,
        max_score=20.0,
        topic_breakdown=stub_topic_breakdown,
    )


# ─── MemoryTutor ───────────────────────────────────────────

@router.post("/tutor")
async def chat_with_tutor(
    body: TutorChatRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Chat with the persistent MemoryTutor.

    Streams a Sonnet response injected with a briefing of the student's
    prior sessions and known weak spots.
    """
    conversation = [m.model_dump() for m in body.conversation]

    return StreamingResponse(
        memory_tutor.chat(
            message=body.message,
            user_id=user.user_id,
            institution_id=user.institution_id or "",
            conversation=conversation,
        ),
        media_type="text/event-stream",
    )


# ─── WeakSpotter ───────────────────────────────────────────

@router.get("/weak-spots", response_model=WeakSpotsResponse)
async def get_weak_spots(user: CurrentUser = Depends(get_current_user)):
    """Retrieve the student's concept gap tracker, ordered weakest first."""
    spots = await weak_spotter.get_weak_spots(user.user_id)
    return WeakSpotsResponse(weak_spots=spots)


# ─── RevisionClock ─────────────────────────────────────────

@router.post("/schedule", response_model=RevisionScheduleResponse)
async def generate_schedule(
    body: RevisionGenerateRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a day-by-day revision schedule up to the exam date."""
    schedule = await revision_clock.generate(
        user_id=user.user_id,
        institution_id=user.institution_id or "",
        exam_date=body.exam_date,
    )
    return RevisionScheduleResponse(
        schedule=schedule,
        exam_date=str(body.exam_date),
    )


@router.get("/schedule", response_model=RevisionScheduleResponse)
async def get_schedule(
    user: CurrentUser = Depends(get_current_user),
):
    """Retrieve the student's existing total revision schedule."""
    data = await revision_clock.get_schedule(user.user_id)
    return RevisionScheduleResponse(
        schedule=data.get("schedule", []),
        exam_date=data.get("exam_date", ""),
    )


@router.post("/schedule/rebalance", response_model=RevisionScheduleResponse)
async def rebalance_schedule(
    body: RebalanceRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Redistribute incomplete tasks from missed days across future days."""
    schedule = await revision_clock.rebalance(
        user.user_id,
        body.missed_dates,
    )
    # Re-fetch to get exam_date
    data = await revision_clock.get_schedule(user.user_id)
    return RevisionScheduleResponse(
        schedule=schedule,
        exam_date=data.get("exam_date", ""),
    )


@router.get("/todos", response_model=TodoListResponse)
async def get_today_todos(
    user: CurrentUser = Depends(get_current_user),
):
    """Get the dynamic daily to-do list derived from the master schedule.
    Automatically seeds today's rows if it's a new day.
    """
    result = await revision_clock.get_today_todos(user.user_id)
    return TodoListResponse(**result)


@router.patch("/todos", response_model=TodoListResponse)
async def update_todo_status(
    body: UpdateTodoRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Mark a daily to-do item as done, skipped, or pending."""
    result = await revision_clock.update_todo_status(
        user.user_id,
        body.task_key,
        body.status,
    )
    return TodoListResponse(**result)


# ─── PaperPatternMiner ─────────────────────────────────────

@router.get("/patterns", response_model=PatternMinerResponse)
async def get_patterns(user: CurrentUser = Depends(get_current_user)):
    """Get exam pattern insights for the student's institution.

    Aggregates historically ingested past-papers and returns topic
    frequency, unit mark distribution, question-type breakdown, and
    year-wise trends.
    """
    result = await paper_pattern_miner.get_patterns(
        institution_id=user.institution_id or "",
    )
    return PatternMinerResponse(**result)


@router.post("/patterns/ingest", response_model=IngestPaperResponse)
async def ingest_paper(
    body: IngestPaperRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Ingest a past exam paper and extract topic-tagged questions.

    Uses Haiku to extract every question, matches each to a syllabus
    topic via Qdrant, and persists the enriched questions to Supabase.
    """
    result = await paper_pattern_miner.ingest_paper(
        paper_text=body.paper_text,
        year=body.year,
        institution_id=user.institution_id or "",
    )
    return IngestPaperResponse(**result)


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
