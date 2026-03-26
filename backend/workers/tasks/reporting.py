"""Batch Assessment Report Generator (Celery Task).

Thin Celery wrapper around engines.iae.report_weaver.ReportWeaver.

Workflow (triggered via POST /faculty/exams/{exam_id}/report):
1. Faculty calls the endpoint → task is queued, HTTP 200 returned immediately
2. Worker runs _generate_async, which delegates to ReportWeaver.generate()
3. ReportWeaver loads submissions, runs GapFinder, calls LLM, renders PDF,
   uploads to R2 and saves the result to Supabase
4. Faculty can refresh GET /faculty/reports to retrieve the finished report
"""

import asyncio

from workers.celery_app import celery_app


async def _generate_async(exam_id: str, institution_id: str, faculty_id: str) -> dict:
    """Delegate to the ReportWeaver engine."""
    from engines.iae.report_weaver import report_weaver
    return await report_weaver.generate(
        exam_id=exam_id,
        institution_id=institution_id,
        faculty_id=faculty_id,
    )


@celery_app.task(name="generate_batch_report", bind=True, max_retries=2)
def generate_batch_report(self, exam_id: str, institution_id: str, faculty_id: str):
    """Celery task: generate and upload a batch performance report for an exam."""
    try:
        result = asyncio.run(_generate_async(exam_id, institution_id, faculty_id))
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
