"""Student-facing API endpoints."""

from fastapi import APIRouter, Depends
from auth import get_current_user, CurrentUser
from models.schemas import (
    CoverageResponse,
    SyllabusResponse,
    ReadinessResponse,
)
from engines.ace.chaos_cleaner import chaos_cleaner
from engines.ace.syllabus_mapper import syllabus_mapper

router = APIRouter()


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
