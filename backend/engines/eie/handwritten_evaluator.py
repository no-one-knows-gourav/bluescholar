"""HandwrittenAnswerEvaluator — OCR + AI Grading Engine.

Pipeline:
1. Download script images from R2
2. OCR each page with pytesseract
3. Segment full OCR text by question number (heuristic)
4. Evaluate each answer against the model answer using claude-sonnet
5. Write provisional grading to Supabase ``exam_submissions``
"""

import json
from core.llm import llm
from core.storage import storage


EVAL_PROMPT = """\
You are grading a student's handwritten exam answer (OCR-transcribed).

Question: {question}
Maximum marks: {max_marks}
Model answer key concepts: {model_answer}

Student's answer (OCR transcription):
{student_answer}

Evaluate and return ONLY this JSON:
{{
  "marks_awarded": <number 0-{max_marks}>,
  "max_marks": {max_marks},
  "feedback": "2-3 sentence feedback for the student",
  "concepts_covered": ["concept1", "concept2"],
  "concepts_missing": ["concept3"],
  "confidence": "high|medium|low"
}}
"""


class HandwrittenAnswerEvaluator:
    """OCR + LLM evaluation of handwritten exam scripts."""

    async def evaluate(
        self,
        script_image_keys: list[str],
        exam_id: str,
        student_id: str,
        institution_id: str,
        exam_questions: list[dict],
    ) -> list[dict]:
        """Evaluate a complete handwritten exam script.

        Args:
            script_image_keys: R2 keys for each scanned page image.
            exam_id: The exam being graded.
            student_id: Student being graded.
            institution_id: Institution slug.
            exam_questions: List of {question_id, question_text, marks, model_answer, order_index}.

        Returns:
            List of per-question grading dicts.
        """
        # 1. OCR all pages
        full_script = await self._ocr_pages(script_image_keys)

        # 2. Evaluate each question
        results: list[dict] = []
        for q in exam_questions:
            student_ans = self._extract_answer(full_script, q.get("order_index", 1), len(exam_questions))
            result = await self._evaluate_question(q, student_ans)
            result["question_id"] = q.get("question_id")
            results.append(result)

        # 3. Compute total and save provisionally
        total_score = sum(r.get("marks_awarded", 0) for r in results)
        await self._save_provisional(student_id, exam_id, total_score, results)

        return results

    # ── Private helpers ────────────────────────────────────────────────────

    async def _ocr_pages(self, image_keys: list[str]) -> str:
        """Download each image from R2 and OCR it with pytesseract."""
        pages: list[str] = []
        for key in image_keys:
            try:
                image_bytes = await storage.download(key)
                text = self._ocr_bytes(image_bytes)
                pages.append(text)
            except Exception:
                pages.append("")
        return "\n--- PAGE BREAK ---\n".join(pages)

    @staticmethod
    def _ocr_bytes(image_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            return pytesseract.image_to_string(img)
        except Exception:
            return ""

    @staticmethod
    def _extract_answer(script: str, order_index: int, total_questions: int) -> str:
        """Heuristic: split script by question markers and return the segment for this question."""
        import re
        # Look for "Q1", "Q 1", "1.", "Question 1", etc.
        pattern = re.compile(
            r"(?:Q\.?\s*" + str(order_index) + r"|Question\s+" + str(order_index) + r"|\b" + str(order_index) + r"\.)",
            re.IGNORECASE,
        )
        next_pattern = re.compile(
            r"(?:Q\.?\s*" + str(order_index + 1) + r"|Question\s+" + str(order_index + 1) + r"|\b" + str(order_index + 1) + r"\.)",
            re.IGNORECASE,
        ) if order_index < total_questions else None

        match = pattern.search(script)
        if not match:
            # Fallback: divide script evenly
            segment_len = max(1, len(script) // total_questions)
            start = (order_index - 1) * segment_len
            return script[start:start + segment_len]

        start = match.end()
        if next_pattern:
            next_match = next_pattern.search(script, start)
            end = next_match.start() if next_match else len(script)
        else:
            end = len(script)

        return script[start:end].strip()

    async def _evaluate_question(self, question: dict, student_answer: str) -> dict:
        max_marks = question.get("marks", 10)
        try:
            resp = await llm.complete(
                model="claude-sonnet-4-20250514",
                system=EVAL_PROMPT.format(
                    question=question.get("question_text", ""),
                    max_marks=max_marks,
                    model_answer=question.get("model_answer", ""),
                    student_answer=student_answer[:3000],
                ),
                user="Evaluate.",
                max_tokens=512,
                temperature=0.1,
            )
            return json.loads(resp.text)
        except Exception:
            return {
                "marks_awarded": 0,
                "max_marks": max_marks,
                "feedback": "Evaluation failed — please review manually.",
                "concepts_covered": [],
                "concepts_missing": [],
                "confidence": "low",
            }

    async def _save_provisional(
        self, student_id: str, exam_id: str, total_score: float, grading_detail: list
    ) -> None:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            (
                sb.table("exam_submissions")
                .update({
                    "score": total_score,
                    "grading_detail": grading_detail,
                    "grading_status": "provisional",
                })
                .eq("student_id", student_id)
                .eq("exam_id", exam_id)
                .execute()
            )
        except Exception:
            pass


# Singleton
handwritten_evaluator = HandwrittenAnswerEvaluator()
