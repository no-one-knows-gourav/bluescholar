"""File upload and document management endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from auth import get_current_user, CurrentUser
from engines.ace.chaos_cleaner import chaos_cleaner
from engines.ace.syllabus_mapper import syllabus_mapper
from models.schemas import UploadResponse, DocumentResponse

router = APIRouter()


@router.post("/student/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    doc_type: str = Query(default="student_note", description="Document type: student_note | syllabus | past_paper"),
    user: CurrentUser = Depends(get_current_user),
):
    """Upload one or more documents for processing.

    Supported formats: PDF, DOCX, PPTX, PNG, JPG, TXT.
    Files are uploaded to R2 and queued for async processing
    (text extraction → chunking → embedding → Qdrant upsert).

    If doc_type is 'syllabus', also triggers SyllabusMapper.
    """
    file_dicts = []
    for file in files:
        content = await file.read()
        file_dicts.append({
            "filename": file.filename,
            "content": content,
            "content_type": file.content_type or "application/octet-stream",
        })

    records = await chaos_cleaner.ingest(
        files=file_dicts,
        user_id=user.user_id,
        institution_id=user.institution_id or "",
    )

    documents = [
        DocumentResponse(
            filename=r["filename"],
            r2_key=r["r2_key"],
            doc_type=r["doc_type"],
            status=r["status"],
        )
        for r in records
    ]

    return UploadResponse(uploaded=len(documents), documents=documents)


@router.get("/student/documents")
async def list_documents(user: CurrentUser = Depends(get_current_user)):
    """List all documents uploaded by the authenticated student.

    Stub — will query Supabase 'documents' table.
    """
    # TODO: Query Supabase for user's documents
    return {"documents": []}
