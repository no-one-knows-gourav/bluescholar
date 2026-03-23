-- ═══════════════════════════════════════════════════════════
-- BlueScholar Database Schema (Supabase / PostgreSQL)
-- Run this in the Supabase SQL Editor to set up all tables.
-- ═══════════════════════════════════════════════════════════

-- ─── Institutions ──────────────────────────────────────────

create table if not exists institutions (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  university text,
  enrollment_code char(6) unique,
  created_by uuid,
  created_at timestamptz default now()
);

-- ─── Profiles (extends auth.users) ────────────────────────

create table if not exists profiles (
  id uuid references auth.users primary key,
  full_name text not null,
  role text not null check (role in ('student', 'faculty', 'admin')),
  institution_id uuid references institutions(id),
  department text,
  roll_number text,
  created_at timestamptz default now()
);

alter table profiles enable row level security;
create policy "Users can view own profile" on profiles
  for select using (auth.uid() = id);
create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);
create policy "Users can insert own profile" on profiles
  for insert with check (auth.uid() = id);

-- ─── Documents ─────────────────────────────────────────────

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  filename text,
  r2_key text,
  doc_type text,
  status text default 'processing',
  chunk_count int,
  created_at timestamptz default now()
);

alter table documents enable row level security;
create policy "Users can view own documents" on documents
  for select using (auth.uid() = user_id);
create policy "Users can insert own documents" on documents
  for insert with check (auth.uid() = user_id);

-- ─── Syllabi ───────────────────────────────────────────────

create table if not exists syllabi (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references institutions(id),
  data jsonb not null,
  created_at timestamptz default now()
);

-- ─── Chat History ──────────────────────────────────────────

create table if not exists chat_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  agent text not null,
  question text,
  response text,
  context_sources jsonb,
  topic_tags jsonb,
  created_at timestamptz default now()
);

alter table chat_history enable row level security;
create policy "Users can view own chat history" on chat_history
  for select using (auth.uid() = user_id);
create policy "Users can insert own chat history" on chat_history
  for insert with check (auth.uid() = user_id);

-- ─── Weak Spots ────────────────────────────────────────────

create table if not exists weak_spots (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  concept text not null,
  unit int,
  score numeric default 0,
  attempt_count int default 0,
  last_updated timestamptz default now()
);

alter table weak_spots enable row level security;
create policy "Users can view own weak spots" on weak_spots
  for select using (auth.uid() = user_id);

-- ─── Question Bank ─────────────────────────────────────────

create table if not exists question_bank (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  question text not null,
  question_type text,
  bloom_level text,
  marks int,
  model_answer text,
  topic text,
  unit int,
  options jsonb,
  source_doc_id uuid references documents(id),
  created_at timestamptz default now()
);

-- ─── Mocks ─────────────────────────────────────────────────

create table if not exists mocks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  question_ids jsonb,
  pdf_key text,
  status text default 'pending',
  answers jsonb,
  score numeric,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz default now()
);

alter table mocks enable row level security;
create policy "Users can view own mocks" on mocks
  for select using (auth.uid() = user_id);

-- ─── Mock Results ──────────────────────────────────────────

create table if not exists mock_results (
  id uuid primary key default gen_random_uuid(),
  mock_id uuid references mocks(id),
  user_id uuid references profiles(id),
  institution_id uuid references institutions(id),
  topic text,
  unit int,
  score numeric,
  max_score numeric
);

-- ─── Revision Schedules ────────────────────────────────────

create table if not exists revision_schedules (
  user_id uuid references profiles(id) primary key,
  schedule jsonb not null,
  exam_date date,
  updated_at timestamptz default now()
);

-- ─── Exams ─────────────────────────────────────────────────

create table if not exists exams (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid references institutions(id),
  created_by uuid references profiles(id),
  title text,
  instructions text,
  time_limit_mins int,
  opens_at timestamptz,
  closes_at timestamptz,
  result_release text default 'manual' check (result_release in ('immediate', 'manual')),
  randomize_questions bool default true,
  status text default 'draft' check (status in ('draft', 'open', 'closed'))
);

create table if not exists exam_questions_map (
  exam_id uuid references exams(id),
  question_id uuid references question_bank(id),
  order_index int,
  marks int,
  primary key (exam_id, question_id)
);

-- ─── Exam Submissions ──────────────────────────────────────

create table if not exists exam_submissions (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid references exams(id),
  student_id uuid references profiles(id),
  answers jsonb,
  started_at timestamptz,
  submitted_at timestamptz,
  integrity_flags jsonb,
  score numeric,
  grading_detail jsonb,
  grading_status text default 'pending'
);

-- ─── Research Reports ──────────────────────────────────────

create table if not exists research_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  topic text,
  report_md text,
  slide_outline text,
  created_at timestamptz default now()
);

-- ─── Faculty Batch Reports ─────────────────────────────────

create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid references exams(id),
  faculty_id uuid references profiles(id),
  r2_key text,
  created_at timestamptz default now()
);

-- ─── Study Predictions ─────────────────────────────────────

create table if not exists study_predictions (
  user_id uuid references profiles(id) primary key,
  peak_windows jsonb,
  updated_at timestamptz default now()
);
