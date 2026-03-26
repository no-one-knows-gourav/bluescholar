"""Faculty-facing API endpoints."""

import json
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from auth import get_current_user, CurrentUser
from core.storage import storage
from models.schemas import (
    CreateExamRequest,
    ExamResponse,
    PlagueScopeResponse,
    GapFinderResponse,
    EvaluateRequest,
    ApproveSubmissionRequest,
    CalibrateRequest,
    CalibrateResponse,
    GradeAsyncResponse,
)

router = APIRouter()


# ─── Courseware ────────────────────────────────────────────────────────────

@router.post("/courseware/upload")
async def upload_courseware(
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    """Upload course materials to the faculty knowledge base."""
    from workers.tasks.ingest import process_document

    uploaded = []
    institution_id = user.institution_id or ""

    for file in files:
        content = await file.read()
        key = f"courseware/{institution_id}/{file.filename}"
        await storage.upload(key, content, file.content_type or "application/octet-stream")
        process_document.delay(
            file_key=key,
            user_id=user.user_id,
            institution_id=institution_id,
            doc_type="courseware",
        )
        uploaded.append({"filename": file.filename, "r2_key": key, "status": "processing"})

    return {"uploaded": len(uploaded), "documents": uploaded}


# ─── Students ──────────────────────────────────────────────────────────────

@router.get("/students")
async def list_students(user: CurrentUser = Depends(get_current_user)):
    """List enrolled students with readiness scores (stub)."""
    return {"students": []}


# ─── ExamArena ─────────────────────────────────────────────────────────────

@router.post("/exams", response_model=ExamResponse)
async def create_exam(
    body: CreateExamRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new exam."""
    import uuid
    from datetime import datetime, timezone
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        row = {
            "id": str(uuid.uuid4()),
            "institution_id": user.institution_id,
            "created_by": user.user_id,
            "title": body.title,
            "instructions": body.instructions,
            "time_limit_mins": body.time_limit_mins,
            "opens_at": body.opens_at.isoformat() if body.opens_at else None,
            "closes_at": body.closes_at.isoformat() if body.closes_at else None,
            "result_release": body.result_release,
            "randomize_questions": body.randomize_questions,
            "status": "draft",
        }
        res = sb.table("exams").insert(row).execute()
        exam = res.data[0] if res.data else row
        return ExamResponse(
            id=exam["id"],
            title=exam["title"],
            status=exam.get("status", "draft"),
            time_limit_mins=exam["time_limit_mins"],
            opens_at=exam.get("opens_at"),
            closes_at=exam.get("closes_at"),
        )
    except Exception as e:
        return ExamResponse(
            id="error",
            title=body.title,
            status="draft",
            time_limit_mins=body.time_limit_mins,
        )


@router.get("/exams")
async def list_exams(user: CurrentUser = Depends(get_current_user)):
    """List all exams for the faculty's institution."""
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        rows = (
            sb.table("exams")
            .select("id, title, status, time_limit_mins, opens_at, closes_at")
            .eq("institution_id", user.institution_id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"exams": rows.data or []}
    except Exception:
        return {"exams": []}


@router.patch("/exams/{exam_id}/status")
async def update_exam_status(
    exam_id: str,
    status: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Open or close an exam (status: 'open' | 'closed')."""
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        sb.table("exams").update({"status": status}).eq("id", exam_id).execute()
    except Exception:
        pass
    return {"exam_id": exam_id, "status": status}


@router.get("/exams/{exam_id}/monitor")
async def monitor_exam(
    exam_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Live student status for a running exam (stub — Realtime via Supabase)."""
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        rows = (
            sb.table("exam_submissions")
            .select("student_id, started_at, submitted_at, grading_status")
            .eq("exam_id", exam_id)
            .execute()
        )
        return {"exam_id": exam_id, "students": rows.data or []}
    except Exception:
        return {"exam_id": exam_id, "students": []}


# ─── Handwritten Evaluator ──────────────────────────────────────────────────

@router.post("/exams/{exam_id}/evaluate/{student_id}")
async def evaluate_script(
    exam_id: str,
    student_id: str,
    body: EvaluateRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """OCR + AI-grade a student's handwritten exam script.

    Provide R2 keys of scanned script pages plus the question list.
    Returns per-question grading with feedback and provisional total.
    """
    from engines.eie.handwritten_evaluator import handwritten_evaluator
    results = await handwritten_evaluator.evaluate(
        script_image_keys=body.image_keys,
        exam_id=exam_id,
        student_id=student_id,
        institution_id=user.institution_id or "",
        exam_questions=body.questions,
    )
    total = sum(r.get("marks_awarded", 0) for r in results)
    return {"exam_id": exam_id, "student_id": student_id, "total_score": total, "results": results}


@router.post("/exams/{exam_id}/grade-async/{student_id}", response_model=GradeAsyncResponse)
async def grade_script_async(
    exam_id: str,
    student_id: str,
    body: EvaluateRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Enqueue handwritten script OCR+grading as a Celery task.

    Returns immediately with a task ID. The worker loads questions from
    exam_questions_map, OCRs the pages, and saves provisional grades.
    Faculty can then review via GET /faculty/exams/{id}/submissions
    and approve via POST /faculty/submissions/{id}/approve.
    """
    from workers.tasks.grading import grade_handwritten_script
    task = grade_handwritten_script.delay(
        exam_id=exam_id,
        student_id=student_id,
        institution_id=user.institution_id or "",
        image_keys=body.image_keys,
    )
    return GradeAsyncResponse(
        task_id=task.id,
        status="queued",
        exam_id=exam_id,
        student_id=student_id,
    )


# ─── PlagueScope ───────────────────────────────────────────────────────────

@router.get("/exams/{exam_id}/plagiarism", response_model=PlagueScopeResponse)
async def check_plagiarism(
    exam_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Run similarity analysis across all submissions for an exam."""
    from engines.eie.plague_scope import plague_scope
    result = await plague_scope.analyze_batch(
        exam_id=exam_id,
        institution_id=user.institution_id or "",
    )
    return PlagueScopeResponse(**result)


# ─── GapFinder ─────────────────────────────────────────────────────────────

@router.get("/gaps", response_model=GapFinderResponse)
async def get_gaps(user: CurrentUser = Depends(get_current_user)):
    """Teaching and curriculum gap analysis for the institution."""
    from engines.iae.gap_finder import gap_finder
    result = await gap_finder.analyze(institution_id=user.institution_id or "")
    return GapFinderResponse(**result)


# ─── ReportWeaver ──────────────────────────────────────────────────────────

@router.post("/exams/{exam_id}/report")
async def generate_report(
    exam_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Enqueue a batch performance report generation for an exam."""
    from workers.tasks.reporting import generate_batch_report
    task = generate_batch_report.delay(
        exam_id=exam_id,
        institution_id=user.institution_id or "",
        faculty_id=user.user_id,
    )
    return {"task_id": task.id, "status": "queued", "exam_id": exam_id}


@router.get("/reports")
async def list_reports(user: CurrentUser = Depends(get_current_user)):
    """List generated batch reports for the faculty's institution."""
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        rows = (
            sb.table("reports")
            .select("*")
            .eq("institution_id", user.institution_id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"reports": rows.data or []}
    except Exception:
        return {"reports": []}


# ─── Submission Approval ────────────────────────────────────────────────────

@router.get("/exams/{exam_id}/submissions")
async def list_submissions(
    exam_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """List all submissions for an exam with grading status."""
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        rows = (
            sb.table("exam_submissions")
            .select("id, student_id, score, grading_status, submitted_at")
            .eq("exam_id", exam_id)
            .execute()
        )
        return {"exam_id": exam_id, "submissions": rows.data or []}
    except Exception:
        return {"exam_id": exam_id, "submissions": []}


@router.post("/submissions/{submission_id}/approve")
async def approve_submission(
    submission_id: str,
    body: ApproveSubmissionRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Faculty sign-off on a graded submission (sets status → final).

    Optionally override the AI-assigned score and add a comment.
    """
    update: dict = {"grading_status": "final"}
    if body.override_score is not None:
        update["score"] = body.override_score
    if body.comment:
        update["faculty_comment"] = body.comment
    try:
        from config import get_settings
        from supabase import create_client
        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        sb.table("exam_submissions").update(update).eq("id", submission_id).execute()
    except Exception:
        pass
    return {"submission_id": submission_id, "grading_status": "final", **update}


# ─── Exam Difficulty Calibrator ─────────────────────────────────────────────

@router.post("/calibrate", response_model=CalibrateResponse)
async def calibrate_exam(
    body: CalibrateRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Analyse Bloom's taxonomy distribution and estimate exam difficulty.

    Returns a 0–10 difficulty score, breakdown by Bloom's level,
    and LLM-generated recommendations for the faculty.
    """
    from engines.iae.difficulty_calibrator import difficulty_calibrator
    result = await difficulty_calibrator.calibrate(
        institution_id=user.institution_id or "",
        exam_id=body.exam_id,
    )
    return CalibrateResponse(**result)
