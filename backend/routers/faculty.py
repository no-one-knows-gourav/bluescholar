"""Faculty-facing API endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File
from auth import get_current_user, CurrentUser
from core.storage import storage

router = APIRouter()


@router.post("/courseware/upload")
async def upload_courseware(
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    """Upload course materials to the faculty knowledge base.

    Accepts PDF, DOCX, PPTX, images, TXT.
    Queues processing via Celery for chunking + embedding.
    """
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

        uploaded.append({
            "filename": file.filename,
            "r2_key": key,
            "status": "processing",
            "doc_type": "courseware",
        })

    return {"uploaded": len(uploaded), "documents": uploaded}


@router.get("/students")
async def list_students(user: CurrentUser = Depends(get_current_user)):
    """List enrolled students with readiness scores.

    Stub — returns empty list until Supabase queries are wired.
    """
    # TODO: Query Supabase profiles table for students in this institution
    return {"students": []}


@router.get("/gaps")
async def get_gaps(user: CurrentUser = Depends(get_current_user)):
    """GapFinder analysis for the institution.

    Stub — will be implemented in Phase 3.
    """
    return {"gaps": [], "total_topics": 0}


@router.get("/reports")
async def list_reports(user: CurrentUser = Depends(get_current_user)):
    """List generated batch reports.

    Stub — will be implemented in Phase 4.
    """
    return {"reports": []}
