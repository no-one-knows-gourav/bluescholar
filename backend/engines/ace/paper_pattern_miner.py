"""PaperPatternMiner — Exam Pattern Analyst.

Two main responsibilities:
1. ``ingest_paper`` — extract questions from past-paper text, match each to a
   syllabus topic via Qdrant embeddings, and persist to the ``exam_questions``
   Supabase table.
2. ``get_patterns`` — aggregate the stored questions and return topic frequency,
   unit mark distribution, question-type breakdown, and yearly trends.
"""

import json
from collections import Counter, defaultdict
from core.llm import llm
from core.vector import qdrant
from core.embeddings import embeddings


QUESTION_EXTRACTION_PROMPT = """\
You are an exam paper analyser. Extract every distinct question from the provided exam paper text.

Return a JSON array ONLY — no preamble, no markdown fences:
[
  {
    "question_text": "Full question as it appears",
    "marks": 5,
    "question_type": "MCQ|short_answer|long_answer|numerical|diagram",
    "topic_hint": "Brief description of the topic being tested"
  }
]

Rules:
1. Include every question, including sub-parts (label them e.g. "Q3(a)").
2. Infer marks from the paper if listed, otherwise estimate based on question length.
3. Return ONLY valid JSON.
"""


class PaperPatternMiner:
    """Mines historical exam papers for topic frequency and mark distribution patterns."""

    # ── Paper Ingestion ────────────────────────────────────────────────────

    async def ingest_paper(
        self, paper_text: str, year: int, institution_id: str
    ) -> dict:
        """Extract questions from a past paper and persist them with topic tags.

        Steps:
        1. Use Haiku to extract question list from raw text.
        2. Embed each question and match to the closest syllabus topic via Qdrant.
        3. Save enriched questions to Supabase ``exam_questions`` table.

        Returns:
            Dict with ``questions_extracted`` count and the enriched questions list.
        """
        # 1. Extract questions with Haiku
        raw_questions = await self._extract_questions(paper_text)
        if not raw_questions:
            return {"questions_extracted": 0, "questions": []}

        # 2. Match each question to its syllabus topic
        enriched: list[dict] = []
        for q in raw_questions:
            topic_match = await self._match_topic(
                q.get("question_text", "") + " " + q.get("topic_hint", ""),
                institution_id,
            )
            enriched.append({
                **q,
                "unit": topic_match.get("unit"),
                "topic": topic_match.get("topic"),
                "year": year,
                "institution_id": institution_id,
            })

        # 3. Persist to Supabase (best-effort)
        saved = await self._save_questions(enriched)

        return {
            "questions_extracted": saved,
            "questions": enriched,
        }

    # ── Pattern Analysis ───────────────────────────────────────────────────

    async def get_patterns(self, institution_id: str) -> dict:
        """Aggregate historical exam questions into pattern insights.

        Returns topic frequency, unit mark distribution, question-type
        breakdown, and year-wise trends.
        """
        questions = await self._load_questions(institution_id)

        if not questions:
            return {
                "topic_frequency": {},
                "unit_marks_distribution": {},
                "question_type_breakdown": {},
                "yearly_trends": {},
                "total_questions": 0,
            }

        topic_counts = Counter(
            q.get("topic") for q in questions if q.get("topic")
        )
        unit_marks: dict[str, int] = defaultdict(int)
        for q in questions:
            unit = q.get("unit")
            if unit is not None:
                unit_marks[str(unit)] += int(q.get("marks") or 0)

        type_counts = Counter(
            q.get("question_type") for q in questions if q.get("question_type")
        )
        yearly = self._compute_yearly_trends(questions)

        return {
            "topic_frequency": dict(topic_counts.most_common(20)),
            "unit_marks_distribution": dict(unit_marks),
            "question_type_breakdown": dict(type_counts),
            "yearly_trends": yearly,
            "total_questions": len(questions),
        }

    # ── Private helpers ────────────────────────────────────────────────────

    async def _extract_questions(self, text: str) -> list[dict]:
        """Call Haiku to extract questions from raw exam paper text."""
        try:
            response = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=QUESTION_EXTRACTION_PROMPT,
                user=text[:6000],
                max_tokens=2048,
                temperature=0.2,
            )
            return json.loads(response.text)
        except json.JSONDecodeError:
            return []
        except Exception:
            return []

    async def _match_topic(self, text: str, institution_id: str) -> dict:
        """Embed ``text`` and find the closest syllabus topic in Qdrant."""
        try:
            vec = await embeddings.embed(text)
            results = await qdrant.search(
                collection=f"{institution_id}_syllabus",
                query=vec,
                limit=1,
                score_threshold=0.40,
            )
            if results:
                payload = results[0].payload
                return {
                    "unit": payload.get("unit"),
                    "topic": payload.get("topic"),
                }
        except Exception:
            pass
        return {"unit": None, "topic": None}

    def _compute_yearly_trends(self, questions: list[dict]) -> dict:
        """Return a dict of year → topic frequency for trend analysis."""
        by_year: dict[str, dict] = defaultdict(lambda: defaultdict(int))
        for q in questions:
            year = str(q.get("year", "unknown"))
            topic = q.get("topic")
            if topic:
                by_year[year][topic] += 1
        return {yr: dict(counts) for yr, counts in by_year.items()}

    async def _save_questions(self, questions: list[dict]) -> int:
        """Persist questions to Supabase ``exam_questions`` table."""
        if not questions:
            return 0
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            sb.table("exam_questions").insert(questions).execute()
            return len(questions)
        except Exception:
            return len(questions)  # counted as generated even if DB write fails

    async def _load_questions(self, institution_id: str) -> list[dict]:
        """Fetch all ingested exam questions for an institution from Supabase."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("exam_questions")
                .select("*")
                .eq("institution_id", institution_id)
                .execute()
            )
            return rows.data or []
        except Exception:
            return []


# Singleton
paper_pattern_miner = PaperPatternMiner()
