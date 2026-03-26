"""Batch Grading Celery Task.

Celery task wrapper around HandwrittenAnswerEvaluator.
Triggered by faculty after uploading scanned exam scripts.

Workflow:
1. Faculty calls POST /faculty/exams/{exam_id}/grade with student_id + R2 image keys
2. This task runs OCR + LLM evaluation asynchronously
3. Results are saved as 'provisional' to exam_submissions
4. Faculty can then review and approve via POST /faculty/submissions/{id}/approve
"""

import asyncio
from workers.celery_app import celery_app


async def _grade_async(
    exam_id: str,
    student_id: str,
    institution_id: str,
    image_keys: list[str],
) -> dict:
    """Async grading pipeline."""
    from config import get_settings
    from supabase import create_client
    from engines.eie.handwritten_evaluator import handwritten_evaluator

    settings = get_settings()
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

    # Load exam questions via exam_questions_map
    mapping = (
        sb.table("exam_questions_map")
        .select("question_id, order_index, marks")
        .eq("exam_id", exam_id)
        .order("order_index")
        .execute()
    )
    q_ids = [r["question_id"] for r in (mapping.data or [])]

    exam_questions: list[dict] = []
    if q_ids:
        qrows = (
            sb.table("question_bank")
            .select("id, question, model_answer, marks")
            .in_("id", q_ids)
            .execute()
        )
        # Build ordered list with order_index from mapping
        order_map = {r["question_id"]: r["order_index"] for r in (mapping.data or [])}
        for qrow in (qrows.data or []):
            exam_questions.append({
                "question_id": qrow["id"],
                "question_text": qrow.get("question", ""),
                "model_answer": qrow.get("model_answer", ""),
                "marks": qrow.get("marks", 10),
                "order_index": order_map.get(qrow["id"], 1),
            })
        exam_questions.sort(key=lambda q: q["order_index"])

    if not exam_questions:
        return {
            "status": "error",
            "message": "No questions found for this exam. Add questions via exam_questions_map first.",
        }

    results = await handwritten_evaluator.evaluate(
        script_image_keys=image_keys,
        exam_id=exam_id,
        student_id=student_id,
        institution_id=institution_id,
        exam_questions=exam_questions,
    )

    total = sum(r.get("marks_awarded", 0) for r in results)
    return {
        "status": "done",
        "exam_id": exam_id,
        "student_id": student_id,
        "total_score": total,
        "questions_graded": len(results),
        "results": results,
    }


@celery_app.task(name="grade_handwritten_script", bind=True, max_retries=2)
def grade_handwritten_script(
    self,
    exam_id: str,
    student_id: str,
    institution_id: str,
    image_keys: list[str],
):
    """Celery task: OCR + AI-grade a student's handwritten exam script.

    Args:
        exam_id: The exam being graded.
        student_id: Student whose script is being graded.
        institution_id: Institution slug.
        image_keys: List of R2 object keys for scanned page images.

    Returns:
        {status, exam_id, student_id, total_score, questions_graded, results}
    """
    try:
        result = asyncio.run(
            _grade_async(exam_id, student_id, institution_id, image_keys)
        )
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
