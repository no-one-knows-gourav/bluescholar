
# BlueScholar Prototype — Implementation Guide
**Version 2.0 | March 2026**

---

## 1. Overview & Scope

This document defines the complete implementation blueprint for the BlueScholar hosted prototype. The prototype supports real student and faculty accounts, covers all five engine groupings from the PRD, and is scoped for lightweight deployment on affordable cloud infrastructure. Every service, model, and integration is specified with concrete providers and implementation notes.

The prototype must demonstrate:
- Self-serve onboarding for both students and faculty
- Faculty-controlled institutional knowledge base
- Student-facing AI preparation loop (upload → study → practice → plan)
- Faculty-facing evaluation loop (ingest → assess → grade → report)
- Multi-tenant data isolation at the database and vector store level

---

## 2. Hosting & Infrastructure

### 2.1 Application Hosting

| Layer | Provider | Tier | Notes |
|---|---|---|---|
| Frontend | **Vercel** | Hobby → Pro | Next.js App Router, edge functions, preview deployments |
| Backend API | **Railway** | Starter ($5/mo) | FastAPI container, auto-deploy from GitHub |
| Background Jobs | **Railway** (separate service) | Starter | Celery worker for long-running tasks |
| Message Queue | **Upstash Redis** | Free → Pay-as-you-go | Celery broker + session cache |
| Object Storage | **Cloudflare R2** | Free tier (10GB) | PDF/image uploads, processed artifacts |
| CDN | **Cloudflare** | Free | Static assets, R2 public bucket |

**Rationale**: Vercel handles the Next.js frontend with zero-config deploys. Railway runs the Python backend with persistent containers (no cold starts). This combination keeps the monthly bill under $30 at prototype scale (< 500 users).

### 2.2 Databases

| Purpose | Provider | Tier | Notes |
|---|---|---|---|
| Primary relational DB | **Supabase** (PostgreSQL) | Free (500MB) → Pro | Users, courses, sessions, submissions, audit logs |
| Vector store | **Qdrant Cloud** | Free (1GB) | Per-tenant collections for document embeddings |
| Key-value / cache | **Upstash Redis** | Free (10k req/day) | Session state, job status, rate limiting |

**Multi-tenancy**: Every Qdrant collection is namespaced as `{institution_slug}_{user_id}_{collection_type}`. Row-level security (RLS) policies in Supabase enforce tenant isolation at the database layer — no application-level filtering is trusted alone.

### 2.3 Environment Configuration

```
# .env.example
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

QDRANT_URL=
QDRANT_API_KEY=

CLOUDFLARE_R2_ACCOUNT_ID=
CLOUDFLARE_R2_ACCESS_KEY_ID=
CLOUDFLARE_R2_SECRET_ACCESS_KEY=
CLOUDFLARE_R2_BUCKET=bluescholar-uploads

UPSTASH_REDIS_URL=
UPSTASH_REDIS_TOKEN=

ANTHROPIC_API_KEY=
OPENAI_API_KEY=               # fallback / embeddings
GOOGLE_GENERATIVE_AI_API_KEY= # optional

CELERY_BROKER_URL=
```

---

## 3. Authentication & Accounts

### 3.1 Auth Provider: Supabase Auth

Supabase Auth handles all identity management. No custom auth server is needed for the prototype.

**Supported flows**:
- Email + password (primary)
- Magic link (passwordless option)
- Google OAuth (optional, add later)

**Role model**: Roles are stored in the `profiles` table (not Supabase's built-in roles) to allow richer institutional context.

```sql
-- profiles table (extends auth.users)
create table profiles (
  id uuid references auth.users primary key,
  full_name text not null,
  role text not null check (role in ('student', 'faculty', 'admin')),
  institution_id uuid references institutions(id),
  department text,
  roll_number text,           -- students only
  created_at timestamptz default now()
);

-- Row-level security: users can only read their own profile
alter table profiles enable row level security;
create policy "own profile" on profiles
  for all using (auth.uid() = id);
```

### 3.2 Onboarding Flows

**Student Registration**:
1. Enter email, password, full name, roll number
2. Select institution from dropdown (faculty must have created institution first)
3. Enter enrollment code (6-digit code faculty shares, stored in `institutions.enrollment_code`)
4. Confirm email → redirect to student dashboard
5. Prompted immediately to upload syllabus PDF to initialize SyllabusMapper

**Faculty Registration**:
1. Enter email, password, full name
2. Create institution (name, university affiliation, department) OR join existing with admin code
3. Confirm email → redirect to faculty dashboard
4. Prompted to upload course materials and set enrollment code for students

**Institution Model**:
```sql
create table institutions (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,       -- used for Qdrant namespace
  university text,
  enrollment_code char(6) unique,  -- students use this to join
  created_by uuid references profiles(id),
  created_at timestamptz default now()
);
```

### 3.3 Session Management

Supabase Auth JWTs are passed as `Authorization: Bearer <token>` to the FastAPI backend. The backend validates via Supabase's JWKS endpoint. A middleware extracts `user_id`, `institution_id`, and `role` from the token on every request — no separate session store needed for auth state.

---

## 4. Frontend Architecture

### 4.1 Tech Stack

| Tool | Purpose |
|---|---|
| **Next.js 14** (App Router) | Framework |
| **TypeScript** | Type safety |
| **Tailwind CSS** | Utility styling |
| **shadcn/ui** | Component primitives |
| **Zustand** | Client state (upload progress, active session) |
| **TanStack Query** | Server state, caching, background refetch |
| **react-dropzone** | File upload UI |
| **react-pdf** | PDF viewer for DocDoubt citations |
| **recharts** | Analytics charts (readiness score, mock performance) |
| **date-fns** | Calendar / revision schedule rendering |

### 4.2 Route Structure

```
app/
├── (auth)/
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── onboarding/page.tsx          # post-signup wizard
│
├── (student)/
│   ├── dashboard/page.tsx           # readiness score, today's tasks
│   ├── library/page.tsx             # ChaosCleaner — uploaded docs
│   ├── syllabus/page.tsx            # SyllabusMapper output
│   ├── doubt/page.tsx               # DocDoubt chat interface
│   ├── tutor/page.tsx               # MemoryTutor chat + history
│   ├── mock/page.tsx                # SmartMock — generate & attempt
│   ├── mock/[id]/page.tsx           # Mock attempt interface
│   ├── mock/[id]/result/page.tsx    # Performance breakdown
│   ├── patterns/page.tsx            # PaperPatternMiner insights
│   ├── planner/page.tsx             # RevisionClock calendar view
│   ├── researcher/page.tsx          # AutoResearcher
│   └── exam/[id]/page.tsx           # ExamArena (live exam)
│
├── (faculty)/
│   ├── dashboard/page.tsx           # Batch overview, recent activity
│   ├── courseware/page.tsx          # ChaosCleaner — course KB
│   ├── students/page.tsx            # Student list, readiness scores
│   ├── exams/page.tsx               # ExamArena management
│   ├── exams/create/page.tsx        # Exam builder
│   ├── exams/[id]/page.tsx          # Live exam monitor
│   ├── grading/page.tsx             # Handwritten scripts queue
│   ├── grading/[submissionId]/page.tsx  # Review & sign off
│   ├── plagiarism/page.tsx          # PlagueScope heatmap
│   ├── gaps/page.tsx                # GapFinder analysis
│   ├── calibrator/page.tsx          # Exam Difficulty Calibrator
│   └── reports/page.tsx             # ReportWeaver output
│
└── api/                             # Next.js API routes (thin proxies to FastAPI)
    ├── upload/route.ts
    └── auth/callback/route.ts
```

### 4.3 Design System

**Aesthetic direction**: Institutional intelligence — clean and data-dense, with confident typography. Think Bloomberg Terminal meets a well-designed academic dashboard. Dark navy sidebar, white/off-white main canvas, a single electric blue accent (`#2563EB`), and amber for warnings/gaps.

**Fonts** (via Google Fonts):
- Display: `DM Serif Display` (headings, scores, key numbers)
- Body: `DM Sans` (UI text, labels)
- Mono: `JetBrains Mono` (citations, code, timestamps)

**Core CSS variables**:
```css
:root {
  --bg-canvas: #F8F9FC;
  --bg-sidebar: #0F1629;
  --bg-card: #FFFFFF;
  --text-primary: #0F1629;
  --text-secondary: #64748B;
  --accent-blue: #2563EB;
  --accent-amber: #D97706;
  --accent-green: #059669;
  --accent-red: #DC2626;
  --border: #E2E8F0;
  --radius: 8px;
}
```

---

## 5. Backend Architecture

### 5.1 FastAPI Application Structure

```
backend/
├── main.py                     # App factory, middleware, CORS
├── auth.py                     # Supabase JWT validation dependency
├── config.py                   # Settings from env vars
│
├── core/
│   ├── storage.py              # R2 upload/download helpers
│   ├── vector.py               # Qdrant client + collection helpers
│   ├── llm.py                  # LLM client factory (Anthropic / OpenAI)
│   ├── embeddings.py           # Embedding model wrapper
│   └── chunker.py              # Document chunking strategies
│
├── engines/
│   ├── ace/                    # Academic Content Engine
│   │   ├── chaos_cleaner.py
│   │   ├── syllabus_mapper.py
│   │   ├── lecture_digest.py
│   │   ├── paper_pattern_miner.py
│   │   └── question_forge.py
│   │
│   ├── lre/                    # Learning Resolution Engine
│   │   ├── doc_doubt.py
│   │   ├── memory_tutor.py
│   │   └── auto_researcher.py
│   │
│   ├── ape/                    # Adaptive Planning Engine
│   │   ├── smart_mock.py
│   │   ├── revision_clock.py
│   │   ├── weak_spotter.py
│   │   └── study_time_predictor.py
│   │
│   ├── eie/                    # Evaluation & Integrity Engine
│   │   ├── exam_arena.py
│   │   ├── guard_eye.py
│   │   ├── plague_scope.py
│   │   ├── handwritten_evaluator.py
│   │   └── code_arena.py
│   │
│   └── iae/                    # Institutional Analytics Engine
│       ├── gap_finder.py
│       ├── report_weaver.py
│       └── difficulty_calibrator.py
│
├── routers/
│   ├── student.py              # Student-facing endpoints
│   ├── faculty.py              # Faculty-facing endpoints
│   ├── uploads.py              # File ingestion pipeline
│   └── exams.py                # Exam session management
│
├── workers/
│   ├── celery_app.py           # Celery configuration
│   └── tasks/
│       ├── ingest.py           # Document processing tasks
│       ├── mock_gen.py         # Mock paper generation
│       ├── grading.py          # Batch grading tasks
│       └── reporting.py        # ReportWeaver tasks
│
└── models/
    └── schemas.py              # Pydantic models for all requests/responses
```

### 5.2 AI Model Strategy

All LLM calls go through a unified `core/llm.py` wrapper that selects the right model and manages retries.

| Task | Model | Provider | Notes |
|---|---|---|---|
| Chat (DocDoubt, MemoryTutor, doubt resolution) | `claude-sonnet-4-20250514` | Anthropic | Streaming responses |
| Document summarization (LectureDigest) | `claude-haiku-4-5-20251001` | Anthropic | Cost-efficient for batch |
| Question generation (QuestionForge) | `claude-haiku-4-5-20251001` | Anthropic | High volume |
| Multi-agent pipeline (AutoResearcher, ReportWeaver) | `claude-sonnet-4-20250514` | Anthropic | Needs reasoning quality |
| Grading assistance (HandwrittenEvaluator) | `claude-sonnet-4-20250514` | Anthropic | Needs rubric alignment |
| Embeddings | `text-embedding-3-small` | OpenAI | 1536 dims, cheap, fast |
| OCR | **Google Cloud Vision API** (Free: 1000 units/mo) | Google | Handwritten script OCR |

**Cost control**:
- Haiku for all single-document, high-volume tasks (digests, question gen, syllabus parsing)
- Sonnet for multi-turn chat, multi-agent pipelines, and grading
- Prompt caching enabled where supported (system prompts are long and repeated)
- All embedding calls batched (up to 100 chunks per API call)
- Celery tasks process documents asynchronously so users aren't waiting for LLM responses

### 5.3 Document Processing Pipeline

Every uploaded document goes through a standardized pipeline managed by a Celery task:

```
Upload to R2
    ↓
Celery task: process_document(file_key, user_id, doc_type)
    ↓
1. Download from R2
2. Extract text (pypdf / python-docx / python-pptx / pytesseract for images)
3. Chunk text (RecursiveCharacterTextSplitter, chunk_size=512, overlap=64)
4. Embed chunks (OpenAI text-embedding-3-small, batched)
5. Upsert to Qdrant collection with metadata:
   {user_id, institution_id, doc_type, source_file, page_number, chunk_index}
6. Update document status in Supabase (processing → ready)
7. Trigger downstream agents (SyllabusMapper if doc_type == 'syllabus', etc.)
```

**Qdrant collections per tenant**:
```
{institution_slug}_{user_id}_notes          # student personal notes
{institution_slug}_{user_id}_exams          # past papers
{institution_slug}_courseware               # faculty-uploaded (shared)
{institution_slug}_syllabus                 # parsed syllabus
```

---

## 6. Feature Implementations

### 6.1 ChaosCleaner — Note Chaos Organiser

**Student flow**: Upload page with drag-and-drop. Accepts PDF, DOCX, PPTX, PNG, JPG, TXT. Multiple files at once.

**Backend**:
```python
# engines/ace/chaos_cleaner.py
class ChaosCleaner:
    async def ingest(self, files: list[UploadedFile], user_id: str, institution_id: str):
        for file in files:
            # 1. Upload raw to R2
            key = f"uploads/{institution_id}/{user_id}/{file.filename}"
            await storage.upload(key, file.content)
            
            # 2. Queue processing task
            process_document.delay(
                file_key=key,
                user_id=user_id,
                institution_id=institution_id,
                doc_type="student_note"
            )
            
            # 3. Insert pending record in Supabase
            await db.documents.insert({
                "user_id": user_id, "r2_key": key,
                "status": "processing", "filename": file.filename
            })
    
    async def get_coverage(self, user_id: str, institution_id: str) -> dict:
        """Cross-reference user's docs against syllabus topics."""
        syllabus_topics = await self._get_syllabus_topics(institution_id)
        user_chunks = await qdrant.scroll(
            collection=f"{institution_id}_{user_id}_notes",
            limit=1000
        )
        # For each syllabus topic, check embedding similarity with user chunks
        coverage = {}
        for topic in syllabus_topics:
            results = await qdrant.search(
                collection=f"{institution_id}_{user_id}_notes",
                query=topic['embedding'],
                limit=3, score_threshold=0.65
            )
            coverage[topic['name']] = "covered" if results else "gap"
        return coverage
```

**UI**: After upload, show a syllabus coverage grid — green for topics with notes, amber for thin coverage, red for gaps. Each cell links to relevant chunks.

---

### 6.2 SyllabusMapper — Intelligent Syllabus Parser

Runs automatically when a student uploads a file tagged as "syllabus", or faculty uploads the official syllabus.

```python
# engines/ace/syllabus_mapper.py
SYLLABUS_PARSE_PROMPT = """
You are parsing a university syllabus PDF. Extract a structured JSON with this schema:
{
  "units": [
    {
      "unit_number": 1,
      "title": "...",
      "weightage_marks": 20,
      "topics": [
        {"name": "...", "subtopics": ["...", "..."], "prerequisite_topics": ["..."]}
      ]
    }
  ],
  "total_marks": 100,
  "exam_duration_hours": 3
}
Return ONLY valid JSON. No preamble.
"""

class SyllabusMapper:
    async def parse(self, syllabus_text: str, institution_id: str) -> dict:
        response = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system=SYLLABUS_PARSE_PROMPT,
            user=syllabus_text[:8000]  # first 8k chars covers most syllabi
        )
        parsed = json.loads(response.text)
        
        # Store in Supabase
        await db.syllabi.upsert({"institution_id": institution_id, "data": parsed})
        
        # Embed each topic for downstream retrieval
        for unit in parsed['units']:
            for topic in unit['topics']:
                embedding = await embeddings.embed(topic['name'] + " " + " ".join(topic['subtopics']))
                await qdrant.upsert(
                    collection=f"{institution_id}_syllabus",
                    id=str(uuid4()),
                    vector=embedding,
                    payload={"unit": unit['unit_number'], "topic": topic['name'], "weightage": unit['weightage_marks']}
                )
        return parsed
```

**UI**: Interactive syllabus tree — collapsible units, weightage badges, prerequisite arrows. Student can click any topic to see related notes (from ChaosCleaner) and past paper appearances (from PaperPatternMiner).

---

### 6.3 DocDoubt — Strict Grounding Q&A

The core student chat feature. Hard constraint: only answers from uploaded material.

```python
# engines/lre/doc_doubt.py
SYSTEM_PROMPT = """
You are DocDoubt, a strictly grounded academic assistant for {student_name}.
You ONLY answer questions using the provided context passages from the student's uploaded course material.
Rules:
1. If the answer is in the context: answer clearly, then cite the source as [Source: {filename}, Page {page}]
2. If partially covered: answer what you can, then say "⚠ Partial coverage — the following aspect is not in your uploaded material: [gap]"
3. If not covered at all: say exactly "✗ This question falls outside your uploaded course material. Consider checking [topic area] in your textbook."
NEVER generate information that is not directly supported by the provided context.
"""

class DocDoubt:
    async def chat(self, question: str, user_id: str, institution_id: str, stream=True):
        # 1. Embed the question
        q_embedding = await embeddings.embed(question)
        
        # 2. Search student notes AND faculty courseware
        student_results = await qdrant.search(
            collection=f"{institution_id}_{user_id}_notes",
            query=q_embedding, limit=5, score_threshold=0.60
        )
        faculty_results = await qdrant.search(
            collection=f"{institution_id}_courseware",
            query=q_embedding, limit=5, score_threshold=0.60
        )
        
        all_results = student_results + faculty_results
        if not all_results:
            yield "✗ This question falls outside your uploaded course material."
            return
        
        # 3. Build context with citations
        context = "\n\n".join([
            f"[Source: {r.payload['filename']}, Page {r.payload.get('page', '?')}]\n{r.payload['text']}"
            for r in all_results
        ])
        
        # 4. Stream response
        async for chunk in llm.stream(
            model="claude-sonnet-4-20250514",
            system=SYSTEM_PROMPT.format(student_name="Student"),
            user=f"Context:\n{context}\n\nQuestion: {question}"
        ):
            yield chunk
        
        # 5. Save to session history (for MemoryTutor)
        await db.chat_history.insert({
            "user_id": user_id, "agent": "doc_doubt",
            "question": question, "context_sources": [r.payload['filename'] for r in all_results]
        })
```

**UI**: Split-pane chat — conversation on left, source PDF viewer on right. When DocDoubt cites a source, clicking the citation opens the PDF scrolled to that page. Citations render as inline chips.

---

### 6.4 MemoryTutor — Persistent Agentic Tutor

Builds a persistent model of the student's gaps across all sessions.

```python
# engines/lre/memory_tutor.py

class MemoryTutor:
    async def get_session_context(self, user_id: str) -> str:
        """Summarize all prior sessions into a tutor briefing."""
        history = await db.chat_history.select(
            user_id=user_id, limit=100, order="created_at desc"
        )
        gaps = await db.weak_spots.select(user_id=user_id, order="score asc", limit=20)
        
        briefing = f"""
Prior session summary:
- Topics covered: {', '.join(set(h['topic_tags'] for h in history if h.get('topic_tags')))}
- Unresolved gaps flagged: {', '.join(g['concept'] for g in gaps[:5])}
- Last session date: {history[0]['created_at'] if history else 'First session'}
"""
        return briefing
    
    async def chat(self, message: str, user_id: str, institution_id: str, 
                   conversation: list[dict], stream=True):
        context = await self.get_session_context(user_id)
        
        system = f"""
You are MemoryTutor, a persistent academic tutor that remembers everything about this student.
{context}

Your behavior:
- Open sessions by referencing unresolved gaps from last time
- Never repeat what the student has mastered
- When a student struggles, flag it internally and address it next session
- At the end of each response, suggest the next concept to tackle
- Ground all explanations in the student's own uploaded course material where possible
"""
        async for chunk in llm.stream(
            model="claude-sonnet-4-20250514",
            system=system,
            messages=conversation + [{"role": "user", "content": message}]
        ):
            yield chunk
```

**UI**: Chat interface with a persistent left sidebar showing "Your Learning Map" — a visual list of topics with mastery indicators (red/amber/green dots). Clicking a topic opens a filtered view of all MemoryTutor exchanges on that concept.

---

### 6.5 PaperPatternMiner — Exam Pattern Analyst

Processes uploaded past papers and surfaces statistical patterns.

```python
# engines/ace/paper_pattern_miner.py

QUESTION_EXTRACTION_PROMPT = """
Extract all questions from this exam paper as JSON array:
[{"question_text": "...", "marks": 5, "question_type": "descriptive|MCQ|numerical|diagram",
  "topic_hint": "..."}]
Return ONLY valid JSON.
"""

class PaperPatternMiner:
    async def ingest_paper(self, paper_text: str, year: int, institution_id: str):
        # Extract questions
        response = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system=QUESTION_EXTRACTION_PROMPT,
            user=paper_text[:6000]
        )
        questions = json.loads(response.text)
        
        # Match each question to syllabus topic via embedding similarity
        for q in questions:
            q_embedding = await embeddings.embed(q['question_text'])
            topic_match = await qdrant.search(
                collection=f"{institution_id}_syllabus",
                query=q_embedding, limit=1
            )
            q['unit'] = topic_match[0].payload['unit'] if topic_match else None
            q['topic'] = topic_match[0].payload['topic'] if topic_match else None
            q['year'] = year
        
        # Store in Supabase
        await db.exam_questions.insert_many(questions)
    
    async def get_patterns(self, institution_id: str) -> dict:
        questions = await db.exam_questions.select(institution_id=institution_id)
        
        # Aggregate by topic
        topic_counts = Counter(q['topic'] for q in questions if q['topic'])
        unit_marks = defaultdict(int)
        for q in questions:
            if q['unit']:
                unit_marks[q['unit']] += q['marks']
        
        return {
            "topic_frequency": dict(topic_counts.most_common(20)),
            "unit_marks_distribution": dict(unit_marks),
            "question_type_breakdown": Counter(q['question_type'] for q in questions),
            "yearly_trends": self._compute_yearly_trends(questions)
        }
```

**UI**: Three-panel view — frequency bar chart (topics by appearance count), unit heatmap (marks concentration), and a natural language query box ("Which topics appeared in every paper?") that calls DocDoubt-style retrieval over the indexed papers.

---

### 6.6 SmartMock — Personalised Mock Paper Generator

```python
# engines/ape/smart_mock.py

class SmartMock:
    async def generate(self, user_id: str, institution_id: str) -> dict:
        # 1. Get syllabus weightage
        syllabus = await db.syllabi.get(institution_id=institution_id)
        
        # 2. Get student's weak spots (WeakSpotter data)
        weak_spots = await db.weak_spots.select(user_id=user_id, order="score asc", limit=10)
        weak_topics = {w['concept']: w['score'] for w in weak_spots}
        
        # 3. Get question bank (QuestionForge output)
        questions = await db.question_bank.select(
            user_id=user_id, institution_id=institution_id
        )
        
        # 4. Build mock paper with weighted selection
        selected = []
        marks_remaining = syllabus['data']['total_marks']
        
        for unit in syllabus['data']['units']:
            unit_budget = unit['weightage_marks']
            unit_questions = [q for q in questions if q['unit'] == unit['unit_number']]
            
            # Overweight weak topics (2x probability)
            weighted_pool = []
            for q in unit_questions:
                weight = 2 if q['topic'] in weak_topics else 1
                weighted_pool.extend([q] * weight)
            
            random.shuffle(weighted_pool)
            allocated = 0
            seen_ids = set()
            for q in weighted_pool:
                if q['id'] not in seen_ids and allocated + q['marks'] <= unit_budget:
                    selected.append(q)
                    seen_ids.add(q['id'])
                    allocated += q['marks']
        
        # 5. Generate PDF
        pdf_key = await self._render_pdf(selected, user_id, institution_id)
        
        # 6. Save mock record
        mock_id = await db.mocks.insert({
            "user_id": user_id, "institution_id": institution_id,
            "question_ids": [q['id'] for q in selected],
            "pdf_key": pdf_key, "status": "pending"
        })
        return {"mock_id": mock_id, "pdf_url": await storage.get_signed_url(pdf_key)}
```

**PDF rendering**: Use `reportlab` (Python) to generate a clean, formatted exam PDF mirroring the institution's exam paper style — header with student name/roll/date, questions numbered, marks in margin, space for answers.

**UI**: "Generate Mock" button on dashboard. Shows past mock history with scores. Mock attempt is a timed interface (no PDF — questions rendered in-browser for tracking). On submission, each answer compared against model answer using semantic similarity → instant score + topic breakdown.

---

### 6.7 RevisionClock — Adaptive Revision Planner

```python
# engines/ape/revision_clock.py

PLANNER_PROMPT = """
Generate a day-by-day revision schedule as JSON.
Input:
- Syllabus: {syllabus}
- Exam date: {exam_date}
- Today: {today}
- Weak topics (prioritize these): {weak_topics}
- Topics with good mock scores (reduce time): {strong_topics}
- Peak study windows for this student: {peak_windows}

Rules:
1. Allocate more time to weak topics and high-weightage units
2. Schedule difficult topics in peak windows
3. Leave 2 days before exam for full revision only
4. Max 4 topics per day
5. Include one rest day per week

Return JSON: [{"date": "YYYY-MM-DD", "tasks": [{"topic": "...", "unit": 1, 
"duration_mins": 60, "priority": "high|medium|low", "type": "study|revise|practice"}]}]
"""

class RevisionClock:
    async def generate(self, user_id: str, institution_id: str, exam_date: date) -> list:
        syllabus = await db.syllabi.get(institution_id=institution_id)
        weak_spots = await db.weak_spots.select(user_id=user_id, order="score asc")
        mock_scores = await db.mock_results.select(user_id=user_id)
        peak_windows = await db.study_predictions.get(user_id=user_id)
        
        response = await llm.complete(
            model="claude-sonnet-4-20250514",
            system=PLANNER_PROMPT.format(
                syllabus=json.dumps(syllabus['data'], indent=2),
                exam_date=str(exam_date),
                today=str(date.today()),
                weak_topics=json.dumps([w['concept'] for w in weak_spots[:10]]),
                strong_topics=json.dumps([s['topic'] for s in mock_scores if s['score'] > 80]),
                peak_windows=json.dumps(peak_windows or "Not enough data yet")
            ),
            user="Generate the revision schedule."
        )
        schedule = json.loads(response.text)
        await db.revision_schedules.upsert({"user_id": user_id, "schedule": schedule, "exam_date": str(exam_date)})
        return schedule
    
    async def rebalance(self, user_id: str, missed_dates: list[str]):
        """Called when student marks a day as missed."""
        current = await db.revision_schedules.get(user_id=user_id)
        # Move missed tasks to remaining days, spreading evenly
        # ... rebalance logic ...
        await db.revision_schedules.update(user_id=user_id, schedule=rebalanced)
```

**UI**: Full calendar view (month/week toggle). Each day shows color-coded topic pills. Student can mark tasks done (strike-through + green check). "I missed today" button triggers rebalance. Exam date is pinned with a countdown badge.

---

### 6.8 QuestionForge — Bloom's-Tagged Question Bank Builder

Runs automatically after ChaosCleaner finishes processing new notes.

```python
# engines/ace/question_forge.py

FORGE_PROMPT = """
Given this academic text passage, generate 5 exam questions spanning all Bloom's Taxonomy levels.
Return JSON array:
[{
  "question": "...",
  "question_type": "MCQ|short_answer|long_answer|numerical",
  "bloom_level": "remember|understand|apply|analyze|evaluate|create",
  "marks": 2,
  "model_answer": "...",
  "topic": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."]  // only for MCQ
}]
"""

class QuestionForge:
    async def forge_from_document(self, doc_id: str, user_id: str, institution_id: str):
        chunks = await qdrant.scroll(
            collection=f"{institution_id}_{user_id}_notes",
            filter={"doc_id": doc_id}, limit=50
        )
        
        all_questions = []
        # Process in batches of 5 chunks
        for batch in chunked(chunks, 5):
            combined_text = "\n\n".join(c.payload['text'] for c in batch)
            response = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=FORGE_PROMPT,
                user=combined_text
            )
            questions = json.loads(response.text)
            for q in questions:
                q['user_id'] = user_id
                q['institution_id'] = institution_id
                q['source_doc_id'] = doc_id
            all_questions.extend(questions)
        
        await db.question_bank.insert_many(all_questions)
        return len(all_questions)
```

---

### 6.9 AutoResearcher — Multi-Agent Report Builder

Five-agent LangGraph pipeline. Each agent has one responsibility.

```python
# engines/lre/auto_researcher.py

class AutoResearcher:
    async def run(self, topic: str, user_id: str) -> AsyncGenerator[str, None]:
        """Streams progress updates and final report."""
        
        yield f"data: {json.dumps({'stage': 'planner', 'status': 'running'})}\n\n"
        
        # Stage 1: Planner
        outline = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system="You are a report planner. Given a topic, output a JSON outline with 5-7 section titles and 2-sentence descriptions. Return only JSON.",
            user=f"Topic: {topic}"
        )
        sections = json.loads(outline.text)
        yield f"data: {json.dumps({'stage': 'planner', 'status': 'done', 'sections': [s['title'] for s in sections]})}\n\n"
        
        # Stage 2: Research (web search via Anthropic API tool use)
        yield f"data: {json.dumps({'stage': 'researcher', 'status': 'running'})}\n\n"
        research_data = await self._research_with_tools(topic, sections)
        yield f"data: {json.dumps({'stage': 'researcher', 'status': 'done'})}\n\n"
        
        # Stage 3: Writer
        yield f"data: {json.dumps({'stage': 'writer', 'status': 'running'})}\n\n"
        draft_sections = []
        for section in sections:
            content = await llm.complete(
                model="claude-sonnet-4-20250514",
                system="Write a well-structured section for an academic report. Be specific, cite the research provided.",
                user=f"Section: {section['title']}\nResearch: {research_data}\nWrite 300-400 words."
            )
            draft_sections.append({"title": section['title'], "content": content.text})
        yield f"data: {json.dumps({'stage': 'writer', 'status': 'done'})}\n\n"
        
        # Stage 4: Editor
        full_draft = "\n\n".join(f"## {s['title']}\n{s['content']}" for s in draft_sections)
        edited = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system="Edit this report draft. Fix transitions, remove repetition, ensure consistent academic tone. Return the improved full report.",
            user=full_draft
        )
        
        # Stage 5: Presentation outline
        outline_md = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system="Convert this report into a PowerPoint slide outline. Format as: SLIDE 1: [Title]\n• Bullet\n• Bullet\nSLIDE 2: ...",
            user=edited.text
        )
        
        # Save and return
        await db.research_reports.insert({
            "user_id": user_id, "topic": topic,
            "report_md": edited.text, "slide_outline": outline_md.text
        })
        
        yield f"data: {json.dumps({'stage': 'done', 'report': edited.text, 'slides': outline_md.text})}\n\n"
```

**UI**: Step-by-step progress bar (Planner → Researcher → Writer → Editor → Presenter) with live updates via Server-Sent Events. Final output shows the full report with a "Copy" button and a "Download as DOCX" option (using `python-docx` on the backend).

---

### 6.10 ExamArena — Live Exam Conductor (Faculty)

**Faculty creates exam**:
```sql
create table exams (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references institutions(id),
  created_by uuid references profiles(id),
  title text not null,
  instructions text,
  time_limit_mins int not null,
  opens_at timestamptz,
  closes_at timestamptz,
  result_release text check (result_release in ('immediate', 'manual')),
  randomize_questions bool default true,
  status text default 'draft' check (status in ('draft', 'open', 'closed'))
);

create table exam_questions_map (
  exam_id uuid references exams(id),
  question_id uuid references question_bank(id),
  order_index int,
  marks int
);

create table exam_submissions (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid references exams(id),
  student_id uuid references profiles(id),
  answers jsonb,                  -- {question_id: answer_text}
  started_at timestamptz,
  submitted_at timestamptz,
  integrity_flags jsonb,          -- GuardEye events
  score numeric,
  grading_status text default 'pending'
);
```

**Student exam interface**:
- Fullscreen enforced via Fullscreen API on exam start
- Auto-save via debounced PUT every 30 seconds to `exam_submissions`
- Countdown timer (client-side with server sync every 60s)
- Section navigator with attempted/unattempted indicators
- On time expiry: auto-submit, show confirmation modal

**GuardEye (browser-side)**:
```typescript
// hooks/useGuardEye.ts
export function useGuardEye(examId: string, studentId: string) {
  const events = useRef<IntegrityEvent[]>([]);
  
  useEffect(() => {
    const log = (type: string, detail?: string) => {
      const event = { type, timestamp: Date.now(), detail };
      events.current.push(event);
      // Batch-send to backend every 10 events
      if (events.current.length % 10 === 0) {
        fetch('/api/exams/integrity', { method: 'POST', body: JSON.stringify({ examId, studentId, events: events.current }) });
      }
    };
    
    document.addEventListener('visibilitychange', () => log('visibility_change', document.visibilityState));
    document.addEventListener('contextmenu', (e) => { e.preventDefault(); log('right_click'); });
    document.addEventListener('copy', (e) => { e.preventDefault(); log('copy_attempt'); });
    document.addEventListener('fullscreenchange', () => { if (!document.fullscreenElement) log('fullscreen_exit'); });
    window.addEventListener('blur', () => log('window_blur'));
    
    return () => { /* remove listeners */ };
  }, []);
}
```

**Faculty live dashboard**: Real-time table (Supabase Realtime subscriptions) showing each student's status (Not Started / In Progress / Submitted), time remaining, and a red badge if GuardEye has flagged events.

---

### 6.11 HandwrittenAnswerEvaluator

```python
# engines/eie/handwritten_evaluator.py

class HandwrittenAnswerEvaluator:
    async def evaluate(self, script_image_keys: list[str], exam_id: str, 
                       student_id: str, institution_id: str):
        
        # 1. OCR each page (Google Cloud Vision)
        all_text = []
        for key in script_image_keys:
            image_bytes = await storage.download(key)
            ocr_result = await vision_client.text_detection(image=image_bytes)
            all_text.append(ocr_result.full_text_annotation.text)
        
        full_script = "\n--- PAGE BREAK ---\n".join(all_text)
        
        # 2. Get exam questions + model answers
        exam_questions = await db.exam_questions_map.select(exam_id=exam_id)
        
        # 3. Evaluate each answer
        EVAL_PROMPT = """
You are evaluating a student's handwritten exam answer.
Question: {question}
Maximum marks: {max_marks}
Model answer concepts: {model_answer}

Student's answer (OCR transcription):
{student_answer}

Evaluate and return JSON:
{{"marks_awarded": <number>, "max_marks": <number>, "feedback": "...", 
  "concepts_covered": ["..."], "concepts_missing": ["..."], "confidence": "high|medium|low"}}
"""
        
        results = []
        for q in exam_questions:
            # Roughly segment student answer by question number
            student_ans = self._extract_answer_for_question(full_script, q['order_index'])
            
            eval_response = await llm.complete(
                model="claude-sonnet-4-20250514",
                system=EVAL_PROMPT.format(
                    question=q['question_text'],
                    max_marks=q['marks'],
                    model_answer=q['model_answer'],
                    student_answer=student_ans
                ),
                user="Evaluate."
            )
            result = json.loads(eval_response.text)
            result['question_id'] = q['question_id']
            results.append(result)
        
        total_score = sum(r['marks_awarded'] for r in results)
        
        # 4. Save provisional grades (pending faculty review)
        await db.exam_submissions.update(
            student_id=student_id, exam_id=exam_id,
            score=total_score, grading_detail=results, grading_status='provisional'
        )
        return results
```

**UI**: Faculty sees a split screen — scanned script on left, AI evaluation on right. Each question shows AI-suggested marks with a reasoning panel. Faculty can override any mark with a single click + optional comment. "Approve All" button to finalize. Approved submissions move to `grading_status: 'final'`.

---

### 6.12 PlagueScope — Submission Similarity Analyser

```python
# engines/eie/plague_scope.py

class PlagueScope:
    async def analyze_batch(self, exam_id: str, institution_id: str) -> dict:
        submissions = await db.exam_submissions.select(exam_id=exam_id)
        
        # Embed all submissions
        embeddings_map = {}
        for sub in submissions:
            combined_text = " ".join(str(v) for v in sub['answers'].values())
            emb = await embeddings.embed(combined_text[:8000])
            embeddings_map[sub['student_id']] = emb
        
        # Compute pairwise cosine similarity
        student_ids = list(embeddings_map.keys())
        similarity_matrix = []
        for i, sid1 in enumerate(student_ids):
            row = []
            for j, sid2 in enumerate(student_ids):
                if i == j:
                    row.append(1.0)
                else:
                    sim = cosine_similarity(embeddings_map[sid1], embeddings_map[sid2])
                    row.append(round(sim, 3))
            similarity_matrix.append(row)
        
        # Flag pairs above threshold (0.85)
        flagged_pairs = []
        for i in range(len(student_ids)):
            for j in range(i+1, len(student_ids)):
                if similarity_matrix[i][j] > 0.85:
                    flagged_pairs.append({
                        "student_a": student_ids[i],
                        "student_b": student_ids[j],
                        "similarity": similarity_matrix[i][j]
                    })
        
        return {
            "student_ids": student_ids,
            "matrix": similarity_matrix,
            "flagged_pairs": flagged_pairs,
            "threshold": 0.85
        }
```

**UI**: Interactive heatmap grid (using recharts `ScatterChart` or a custom SVG grid). Cells color-coded from white (0) → amber (0.7) → red (1.0). Clicking a flagged cell opens a side-by-side answer comparison with highlighted similar passages.

---

### 6.13 GapFinder — Teaching Gap Detector

```python
# engines/iae/gap_finder.py

class GapFinder:
    async def analyze(self, institution_id: str) -> dict:
        # Index 1: What was taught (faculty courseware)
        # Index 2: What was examined (past papers + mock results)
        
        syllabus_topics = await db.syllabi.get(institution_id=institution_id)
        
        gaps = []
        for unit in syllabus_topics['data']['units']:
            for topic in unit['topics']:
                topic_embedding = await embeddings.embed(topic['name'])
                
                # Coverage in courseware
                courseware_results = await qdrant.search(
                    collection=f"{institution_id}_courseware",
                    query=topic_embedding, limit=3, score_threshold=0.65
                )
                
                # Coverage in past exams
                exam_results = await qdrant.search(
                    collection=f"{institution_id}_exams",
                    query=topic_embedding, limit=3, score_threshold=0.65
                )
                
                # Mock performance on this topic
                mock_scores = await db.mock_results.aggregate_by_topic(
                    institution_id=institution_id, topic=topic['name']
                )
                avg_mock_score = mock_scores.get('avg', None)
                
                gap_type = None
                if not courseware_results and exam_results:
                    gap_type = "coverage_gap"  # Examined but not taught
                elif courseware_results and avg_mock_score and avg_mock_score < 50:
                    gap_type = "performance_gap"  # Taught but students fail
                elif not courseware_results and not exam_results:
                    gap_type = "blind_spot"  # On syllabus, never seen
                
                if gap_type:
                    gaps.append({
                        "topic": topic['name'],
                        "unit": unit['unit_number'],
                        "gap_type": gap_type,
                        "weightage": unit['weightage_marks'],
                        "avg_mock_score": avg_mock_score,
                        "courseware_coverage": len(courseware_results),
                        "exam_frequency": len(exam_results)
                    })
        
        return {"gaps": gaps, "total_topics": sum(len(u['topics']) for u in syllabus_topics['data']['units'])}
```

**UI**: Faculty dashboard with four color-coded cards (Coverage Gap / Performance Gap / Depth Gap / Blind Spot), each listing affected topics with unit tags and weightage. Clicking a gap card shows which courseware sections are thin and suggests "Consider adding more material on X".

---

### 6.14 ReportWeaver — Automated Batch Report

Runs as a Celery task at end of assessment cycle.

```python
# workers/tasks/reporting.py
@celery.task
async def generate_batch_report(exam_id: str, institution_id: str, faculty_id: str):
    submissions = await db.exam_submissions.select(exam_id=exam_id, grading_status='final')
    gap_analysis = await gap_finder.analyze(institution_id)
    
    REPORT_PROMPT = """
Generate a professional faculty batch performance report in Markdown format.

Data:
- Total students: {total}
- Average score: {avg:.1f}%
- Score distribution: {distribution}
- Topic-wise performance: {topic_scores}
- Learning gaps: {gaps}

Include:
1. Executive Summary (3-4 sentences)
2. Score Distribution Analysis
3. Topic-Wise Breakdown (table format)
4. At-Risk Student Flags (score < 40%)
5. Recommended Interventions
6. Comparison to previous cycle (if data available)

Write in formal academic report style.
"""
    
    response = await llm.complete(
        model="claude-sonnet-4-20250514",
        system=REPORT_PROMPT.format(**aggregated_data),
        user="Generate the report."
    )
    
    # Convert Markdown to PDF using weasyprint
    pdf_bytes = markdown_to_pdf(response.text)
    pdf_key = f"reports/{institution_id}/{exam_id}/batch_report.pdf"
    await storage.upload(pdf_key, pdf_bytes)
    
    await db.reports.insert({"exam_id": exam_id, "faculty_id": faculty_id, "r2_key": pdf_key})
    # Notify faculty via Supabase Realtime
```

---

## 7. Database Schema (Supabase)

```sql
-- Core tables

create table institutions (
  id uuid primary key default gen_random_uuid(),
  name text not null, slug text unique not null,
  university text, enrollment_code char(6) unique,
  created_by uuid, created_at timestamptz default now()
);

create table profiles (
  id uuid references auth.users primary key,
  full_name text not null, role text not null,
  institution_id uuid references institutions(id),
  department text, roll_number text,
  created_at timestamptz default now()
);

create table documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  filename text, r2_key text, doc_type text,
  status text default 'processing',
  chunk_count int, created_at timestamptz default now()
);

create table syllabi (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references institutions(id),
  data jsonb not null,  -- structured syllabus
  created_at timestamptz default now()
);

create table chat_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  agent text not null,  -- doc_doubt | memory_tutor | auto_researcher
  question text, response text,
  context_sources jsonb,
  topic_tags jsonb,
  created_at timestamptz default now()
);

create table weak_spots (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  concept text not null, unit int,
  score numeric default 0,  -- 0-100, lower = weaker
  attempt_count int default 0,
  last_updated timestamptz default now()
);

create table question_bank (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  question text not null, question_type text,
  bloom_level text, marks int,
  model_answer text, topic text, unit int,
  options jsonb,  -- MCQ options
  source_doc_id uuid references documents(id),
  created_at timestamptz default now()
);

create table mocks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  question_ids jsonb, pdf_key text,
  status text default 'pending',
  answers jsonb, score numeric,
  started_at timestamptz, completed_at timestamptz,
  created_at timestamptz default now()
);

create table mock_results (
  id uuid primary key default gen_random_uuid(),
  mock_id uuid references mocks(id),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  topic text, unit int, score numeric, max_score numeric
);

create table revision_schedules (
  user_id uuid references profiles(id) primary key,
  schedule jsonb not null,
  exam_date date,
  updated_at timestamptz default now()
);

create table exams (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references institutions(id),
  created_by uuid references profiles(id),
  title text, instructions text,
  time_limit_mins int, opens_at timestamptz, closes_at timestamptz,
  result_release text default 'manual',
  randomize_questions bool default true,
  status text default 'draft'
);

create table exam_submissions (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid references exams(id),
  student_id uuid references profiles(id),
  answers jsonb, started_at timestamptz, submitted_at timestamptz,
  integrity_flags jsonb, score numeric,
  grading_detail jsonb, grading_status text default 'pending'
);

create table research_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  topic text, report_md text, slide_outline text,
  created_at timestamptz default now()
);

create table reports (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid references exams(id),
  faculty_id uuid references profiles(id),
  r2_key text, created_at timestamptz default now()
);
```

---

## 8. API Reference

All endpoints are prefixed `/api/v1/`. Authentication via `Authorization: Bearer <supabase_jwt>`.

### Student Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/student/upload` | Upload documents (multipart) |
| GET | `/student/documents` | List all uploaded documents |
| GET | `/student/coverage` | Syllabus coverage map |
| POST | `/student/doubt` | DocDoubt question (streaming SSE) |
| POST | `/student/tutor` | MemoryTutor chat message (streaming SSE) |
| GET | `/student/patterns` | PaperPatternMiner insights |
| POST | `/student/mock/generate` | Generate SmartMock paper |
| GET | `/student/mock/{id}` | Get mock paper |
| POST | `/student/mock/{id}/submit` | Submit mock answers |
| GET | `/student/weak-spots` | WeakSpotter current map |
| GET | `/student/schedule` | RevisionClock schedule |
| POST | `/student/schedule/rebalance` | Trigger rebalance (missed day) |
| POST | `/student/research` | AutoResearcher (streaming SSE) |
| GET | `/student/research` | Past research reports |
| GET | `/student/readiness` | Current readiness score (0-100) |

### Faculty Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/faculty/courseware/upload` | Upload course materials |
| GET | `/faculty/students` | List enrolled students with readiness |
| POST | `/faculty/exams` | Create exam |
| GET | `/faculty/exams/{id}/live` | Live exam dashboard |
| GET | `/faculty/exams/{id}/submissions` | All submissions |
| POST | `/faculty/exams/{id}/grade` | Trigger HandwrittenEvaluator |
| POST | `/faculty/submissions/{id}/approve` | Faculty sign-off on grade |
| GET | `/faculty/plagiarism/{exam_id}` | PlagueScope analysis |
| GET | `/faculty/gaps` | GapFinder analysis |
| POST | `/faculty/reports/{exam_id}` | Generate ReportWeaver report |
| GET | `/faculty/reports` | Past reports |
| POST | `/faculty/calibrate` | Exam Difficulty Calibrator |

---

## 9. Readiness Score Computation

The readiness score (0-100) is the student's primary dashboard metric. It updates after every mock, tutor session, and study session.

```python
def compute_readiness(
    mock_scores: list[float],       # recent mock percentages
    weak_spot_coverage: float,      # % of weak spots with improvement
    session_consistency: float,     # days active / days since signup
    days_to_exam: int,
    syllabus_coverage: float        # % of syllabus topics with notes
) -> float:
    
    # Weighted components
    mock_component = np.mean(mock_scores[-3:]) if mock_scores else 0  # last 3 mocks
    gap_component = weak_spot_coverage * 100
    consistency_component = min(session_consistency * 100, 100)
    coverage_component = syllabus_coverage * 100
    
    # Time decay: score deflates as exam approaches if gaps remain
    urgency_penalty = max(0, (10 - days_to_exam) * 2) if days_to_exam < 10 else 0
    
    raw_score = (
        mock_component * 0.40 +
        gap_component * 0.25 +
        consistency_component * 0.20 +
        coverage_component * 0.15
    ) - urgency_penalty
    
    return max(0, min(100, round(raw_score, 1)))
```

---

## 10. Deployment

### 10.1 Repositories

```
bluescholar/
├── frontend/          # Next.js app → deploy to Vercel
├── backend/           # FastAPI app → deploy to Railway
└── worker/            # Celery worker → deploy to Railway (separate service)
```

### 10.2 Vercel Configuration (`frontend/vercel.json`)

```json
{
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase_url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase_anon_key",
    "NEXT_PUBLIC_API_URL": "@backend_url"
  }
}
```

### 10.3 Railway Configuration (`railway.toml`)

```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "on_failure"
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libmagic1 tesseract-ocr
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 10.4 Worker Service (Railway, separate deployment)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
```

### 10.5 Cost Estimate (Prototype Scale, ~200 active users)

| Service | Monthly Cost |
|---|---|
| Vercel Hobby | $0 |
| Railway (backend + worker) | ~$10 |
| Supabase Free | $0 |
| Qdrant Cloud Free | $0 |
| Cloudflare R2 | $0 (< 10GB) |
| Upstash Redis | $0 (free tier) |
| Anthropic API (~500K tokens/day) | ~$15 |
| OpenAI Embeddings | ~$3 |
| Google Cloud Vision (1000 OCR free) | $0 |
| **Total** | **~$28/month** |

---

## 11. Key Dependencies (`requirements.txt`)

```
fastapi==0.115.0
uvicorn==0.30.0
python-multipart==0.0.9
supabase==2.4.0
qdrant-client==1.9.0
anthropic==0.27.0
openai==1.30.0
celery==5.3.6
redis==5.0.4
boto3==1.34.0                    # R2 via S3-compatible API
pypdf==4.2.0
python-docx==1.1.0
python-pptx==0.6.23
Pillow==10.3.0
pytesseract==0.3.10
google-cloud-vision==3.7.0
numpy==1.26.4
scikit-learn==1.4.2
reportlab==4.2.0                 # PDF generation for mocks
weasyprint==62.3                 # Markdown → PDF for reports
langchain==0.2.0
langchain-anthropic==0.1.15
langgraph==0.1.1
```

---

## 12. Development Setup

```bash
# 1. Clone and set up environment
git clone https://github.com/your-org/bluescholar
cd bluescholar

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your keys

# 3. Start local services (or use cloud free tiers directly)
# Qdrant local for dev:
docker run -p 6333:6333 qdrant/qdrant

# Redis local:
docker run -p 6379:6379 redis:alpine

# 4. Run backend
uvicorn main:app --reload

# 5. Run Celery worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info

# 6. Frontend
cd ../frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---

## 13. Feature Rollout Priority

Build in this order to get a working end-to-end loop as fast as possible:

| Phase | Features | Milestone |
|---|---|---|
| **Week 1-2** | Auth, onboarding, ChaosCleaner, SyllabusMapper | Students can upload and see organized notes |
| **Week 3** | DocDoubt, LectureDigest | Students can ask questions |
| **Week 4** | QuestionForge, SmartMock, PaperPatternMiner | Students can practice |
| **Week 5** | MemoryTutor, WeakSpotter, RevisionClock | Full student prep loop |
| **Week 6** | ExamArena, GuardEye, faculty courseware | Faculty can run exams |
| **Week 7** | PlagueScope, HandwrittenEvaluator, GapFinder | Faculty evaluation loop |
| **Week 8** | ReportWeaver, AutoResearcher, readiness score | Full platform demo-ready |

---

*BlueScholar Prototype.md v2.0 — Built for real deployment.*