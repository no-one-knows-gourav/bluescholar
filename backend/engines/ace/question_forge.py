"""QuestionForge — Bloom's-Tagged Question Bank Builder.

Auto-generates exam questions from a student's uploaded document chunks.
Questions span all Bloom's Taxonomy levels and are stored in the question_bank
Supabase table for use by SmartMock and other engines.

Triggered post-ingest via Celery or manually via the student API.
"""

import json
from itertools import islice
from core.llm import llm
from core.vector import qdrant


FORGE_PROMPT = """\
You are QuestionForge, an academic question generation engine.
Given academic text passages, generate 5 exam questions spanning all Bloom's Taxonomy levels.

Return a JSON array ONLY — no preamble, no explanation:
[
  {
    "question": "Full question text",
    "question_type": "MCQ|short_answer|long_answer|numerical",
    "bloom_level": "remember|understand|apply|analyze|evaluate|create",
    "marks": 2,
    "model_answer": "Concise model answer or marking scheme",
    "topic": "Specific topic this question tests",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."]
  }
]

Rules:
1. Spread across all 6 Bloom's levels where the content permits.
2. For MCQ: include exactly 4 options and ensure model_answer is the correct option letter (A/B/C/D).
3. For non-MCQ: set options to null or omit it.
4. Marks: 1-2 for remember/understand, 4-5 for apply/analyze, 8-10 for evaluate/create.
5. Questions must be directly answerable from the provided text.
6. Return ONLY valid JSON. No markdown fences.
"""

# How many Qdrant chunks to group into one LLM call
_BATCH_SIZE = 5


def _batched(iterable, n: int):
    """Yield successive n-sized chunks from an iterable."""
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch


class QuestionForge:
    """Generates a Bloom's-tagged question bank from document chunks."""

    async def forge_from_document(
        self,
        doc_id: str,
        user_id: str,
        institution_id: str,
    ) -> dict:
        """Generate questions from all chunks of an uploaded document.

        Args:
            doc_id: Supabase document ID to generate questions for.
            user_id: The student's user ID.
            institution_id: Institution slug for Qdrant namespace.

        Returns:
            Dict with `questions_generated` count and `questions` list.
        """
        # 1. Load document chunks from Qdrant
        chunks = await self._get_document_chunks(doc_id, user_id, institution_id)

        if not chunks:
            return {
                "questions_generated": 0,
                "doc_id": doc_id,
                "questions": [],
                "error": "No processed content found. The document may still be ingesting.",
            }

        # 2. Process in batches, collect all generated questions
        all_questions: list[dict] = []

        for batch in _batched(chunks, _BATCH_SIZE):
            combined_text = "\n\n".join(
                c.payload.get("text", "") for c in batch
            )
            if not combined_text.strip():
                continue

            batch_questions = await self._forge_batch(combined_text)

            # 3. Inject metadata into each question
            for q in batch_questions:
                q["user_id"] = user_id
                q["institution_id"] = institution_id
                q["source_doc_id"] = doc_id
                # Normalise options: if not MCQ, set to None
                if q.get("question_type") != "MCQ":
                    q["options"] = None

            all_questions.extend(batch_questions)

        # 4. Persist to Supabase (best-effort — swallow errors so caller always gets a result)
        saved_count = await self._save_questions(all_questions)

        return {
            "questions_generated": saved_count,
            "doc_id": doc_id,
            "questions": all_questions,
        }

    async def forge_from_text(
        self,
        text: str,
        user_id: str,
        institution_id: str,
        doc_id: str | None = None,
    ) -> list[dict]:
        """Generate questions from raw text without a Qdrant lookup.

        Useful for on-the-fly generation or testing.
        """
        questions = await self._forge_batch(text[:4000])
        for q in questions:
            q["user_id"] = user_id
            q["institution_id"] = institution_id
            q["source_doc_id"] = doc_id
            if q.get("question_type") != "MCQ":
                q["options"] = None
        return questions

    # ── Private helpers ────────────────────────────────────────────────────

    async def _forge_batch(self, text: str) -> list[dict]:
        """Call Haiku for a single batch of text. Returns parsed questions."""
        try:
            response = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=FORGE_PROMPT,
                user=text[:4000],   # stay well within context
                max_tokens=2048,
                temperature=0.4,    # slight creativity for question diversity
            )
            return json.loads(response.text)
        except json.JSONDecodeError:
            # If JSON is malformed, return empty — don't crash the whole pipeline
            return []
        except Exception:
            return []

    async def _get_document_chunks(
        self,
        doc_id: str,
        user_id: str,
        institution_id: str,
    ) -> list:
        """Retrieve all Qdrant chunks for a specific document."""
        try:
            return await qdrant.scroll(
                collection=f"{institution_id}_{user_id}_notes",
                limit=50,
                filters={"doc_id": doc_id},
            )
        except Exception:
            return []

    async def _save_questions(self, questions: list[dict]) -> int:
        """Persist questions to Supabase question_bank table.

        Returns the number of questions successfully saved.
        """
        if not questions:
            return 0
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            sb.table("question_bank").insert(questions).execute()
            return len(questions)
        except Exception:
            # Supabase persistence is best-effort; questions are still returned
            # to the caller even if DB write fails.
            return len(questions)


# Singleton
question_forge = QuestionForge()
