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


# ─── DocDoubt ───────────────────────────────────────────────

class DoubtRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class DoubtSourceCitation(BaseModel):
    filename: str
    page: int | str | None = None
    score: float
    text_preview: str = ""
    source_type: str = "note"


# ─── LectureDigest ─────────────────────────────────────────

class DigestKeyConcept(BaseModel):
    concept: str
    explanation: str


class DigestDefinition(BaseModel):
    term: str
    definition: str


class DigestFormula(BaseModel):
    name: str
    formula: str
    context: str = ""


class DigestResponse(BaseModel):
    title: str = ""
    summary: str = ""
    key_concepts: list[DigestKeyConcept] = []
    definitions: list[DigestDefinition] = []
    formulas: list[DigestFormula] = []
    review_questions: list[str] = []
    error: str | None = None


# ─── QuestionForge ────────────────────────────────────────

class ForgedQuestion(BaseModel):
    question: str
    question_type: str  # MCQ | short_answer | long_answer | numerical
    bloom_level: str    # remember | understand | apply | analyze | evaluate | create
    marks: int
    model_answer: str
    topic: str
    options: list[str] | None = None  # MCQ only
    user_id: str | None = None
    institution_id: str | None = None
    source_doc_id: str | None = None


class ForgeResponse(BaseModel):
    questions_generated: int
    doc_id: str
    questions: list[ForgedQuestion]
    error: str | None = None


class QuestionListResponse(BaseModel):
    questions: list[ForgedQuestion]
    total: int


# ─── SmartMock ─────────────────────────────────────────────

class MockGenerateResponse(BaseModel):
    mock_id: str | None = None
    pdf_url: str | None = None
    questions: list[dict] = []
    error: str | None = None


class MockSubmitRequest(BaseModel):
    answers: dict[str, str]  # question_id -> answer_text


# ─── PaperPatternMiner ──────────────────────────────────────

class IngestPaperRequest(BaseModel):
    paper_text: str
    year: int


class PatternMinerResponse(BaseModel):
    topic_frequency: dict[str, int] = {}
    unit_marks_distribution: dict[str, int] = {}
    question_type_breakdown: dict[str, int] = {}
    yearly_trends: dict[str, dict] = {}
    total_questions: int = 0


class IngestPaperResponse(BaseModel):
    questions_extracted: int
    questions: list[dict] = []


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
