"""Pydantic models for all API requests and responses."""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# ─── Auth & Profiles ────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    role: str = Field(..., pattern="^(student|faculty)$")
    institution_id: str | None = None
    enrollment_code: str | None = None  # students only
    department: str | None = None
    roll_number: str | None = None


class ProfileResponse(BaseModel):
    id: str
    full_name: str
    role: str
    institution_id: str | None = None
    department: str | None = None
    roll_number: str | None = None


# ─── Institutions ───────────────────────────────────────────

class CreateInstitutionRequest(BaseModel):
    name: str
    university: str | None = None
    department: str | None = None


class InstitutionResponse(BaseModel):
    id: str
    name: str
    slug: str
    university: str | None = None
    enrollment_code: str


# ─── Documents ──────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str | None = None
    filename: str
    r2_key: str
    doc_type: str
    status: str
    chunk_count: int | None = None
    created_at: datetime | None = None


class UploadResponse(BaseModel):
    uploaded: int
    documents: list[DocumentResponse]


# ─── Coverage ───────────────────────────────────────────────

class TopicCoverage(BaseModel):
    status: str  # covered | partial | gap
    unit: int | None = None
    match_count: int = 0
    top_score: float | None = None


class CoverageResponse(BaseModel):
    coverage: dict[str, TopicCoverage]


# ─── Syllabus ───────────────────────────────────────────────

class SyllabusTopic(BaseModel):
    name: str
    subtopics: list[str] = []
    prerequisite_topics: list[str] = []


class SyllabusUnit(BaseModel):
    unit_number: int
    title: str
    weightage_marks: int = 0
    topics: list[SyllabusTopic]


class SyllabusResponse(BaseModel):
    units: list[SyllabusUnit]
    total_marks: int | None = None
    exam_duration_hours: float | None = None


# ─── Chat ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


# ─── Mocks ──────────────────────────────────────────────────

class MockGenerateResponse(BaseModel):
    mock_id: str
    pdf_url: str


class MockSubmitRequest(BaseModel):
    answers: dict[str, str]  # question_id -> answer_text


# ─── Exams ──────────────────────────────────────────────────

class CreateExamRequest(BaseModel):
    title: str
    instructions: str | None = None
    time_limit_mins: int
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    result_release: str = "manual"
    randomize_questions: bool = True


class ExamResponse(BaseModel):
    id: str
    title: str
    status: str
    time_limit_mins: int
    opens_at: datetime | None = None
    closes_at: datetime | None = None


# ─── Readiness ──────────────────────────────────────────────

class ReadinessResponse(BaseModel):
    score: float
    mock_component: float
    gap_component: float
    consistency_component: float
    coverage_component: float
