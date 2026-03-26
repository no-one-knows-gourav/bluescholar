"""Pydantic models for all API requests and responses."""

from pydantic import BaseModel, Field
from datetime import datetime, date
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


# ─── MemoryTutor ────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class TutorChatRequest(BaseModel):
    message: str
    conversation: list[ChatMessage] = []


# ─── WeakSpotter ────────────────────────────────────────────

class WeakSpot(BaseModel):
    concept: str
    unit: int | None = None
    score: float
    attempt_count: int
    last_updated: datetime


class WeakSpotsResponse(BaseModel):
    weak_spots: list[WeakSpot]


class MockTopicScore(BaseModel):
    topic: str
    unit: int | None = None
    score: float
    max_score: float


class MockSubmitResponse(BaseModel):
    score: float
    max_score: float
    topic_breakdown: list[MockTopicScore]


# ─── RevisionClock ──────────────────────────────────────────

class RevisionGenerateRequest(BaseModel):
    exam_date: date


class RevisionTask(BaseModel):
    topic: str
    unit: int | None = None
    duration_mins: int = 60
    priority: str = "medium"
    type: str = "study"


class RevisionDay(BaseModel):
    date: str
    tasks: list[RevisionTask]


class RevisionScheduleResponse(BaseModel):
    schedule: list[RevisionDay]
    exam_date: str


class RebalanceRequest(BaseModel):
    missed_dates: list[str]


class TodoItem(BaseModel):
    task_key: str
    topic: str
    unit: int | None = None
    duration_mins: int = 60
    priority: str = "medium"
    type: str = "study"
    status: str = "pending"


class TodoListResponse(BaseModel):
    date: str
    todos: list[TodoItem]
    completion_rate: float


class UpdateTodoRequest(BaseModel):
    task_key: str
    status: str


# ─── AutoResearcher ─────────────────────────────────────────

class ResearchRequest(BaseModel):
    topic: str


# ─── ExamArena (student-side) ────────────────────────────────

class ExamStartResponse(BaseModel):
    submission_id: str
    exam_id: str
    started_at: str


class AutosaveRequest(BaseModel):
    answers: dict[str, str]  # question_id → answer_text


class SubmitExamRequest(BaseModel):
    answers: dict[str, str]  # final answers


class IntegrityEventRequest(BaseModel):
    exam_id: str
    student_id: str
    events: list[dict]


# ─── PlagueScope ────────────────────────────────────────────

class FlaggedPair(BaseModel):
    student_a: str
    student_b: str
    similarity: float


class PlagueScopeResponse(BaseModel):
    student_ids: list[str]
    matrix: list[list[float]]
    flagged_pairs: list[FlaggedPair]
    threshold: float


# ─── GapFinder ──────────────────────────────────────────────

class GapItem(BaseModel):
    topic: str
    unit: int | None = None
    gap_type: str
    weightage: int | None = None
    avg_mock_score: float | None = None
    courseware_coverage: int
    exam_frequency: int


class GapFinderResponse(BaseModel):
    gaps: list[GapItem]
    total_topics: int


# ─── HandwrittenEvaluator ────────────────────────────────────

class ExamQuestionPayload(BaseModel):
    question_id: str
    question_text: str
    marks: int
    model_answer: str
    order_index: int


class EvaluateRequest(BaseModel):
    image_keys: list[str]   # R2 keys of scanned script pages
    questions: list[ExamQuestionPayload]


# ─── Week 7: Readiness + Calibrator ────────────────────────

class ReadinessResponse(BaseModel):
    score: float
    mock_component: float
    gap_component: float
    consistency_component: float
    coverage_component: float
    days_to_exam: int = 999


class ApproveSubmissionRequest(BaseModel):
    override_score: float | None = None
    comment: str | None = None


class CalibrateRequest(BaseModel):
    exam_id: str | None = None  # optional — if None, calibrates full question bank


class CalibrateResponse(BaseModel):
    difficulty_score: float
    bloom_distribution: dict[str, float]
    total_questions: int
    recommended_adjustments: list[str]


# ─── StudyTimePredictor ──────────────────────────────────────

class StudyTimePredictorResponse(BaseModel):
    hour_distribution: dict[str, int]
    peak_hours: list[int]
    peak_windows: list[str]
    data_points: int


# ─── GradeAsyncResponse ──────────────────────────────────────

class GradeAsyncResponse(BaseModel):
    task_id: str
    status: str
    exam_id: str
    student_id: str


# ─── MockAsyncResponse ───────────────────────────────────────

class MockAsyncResponse(BaseModel):
    task_id: str
    status: str
    message: str = "Mock paper is being generated. Poll GET /student/mock/{mock_id} for readiness."
