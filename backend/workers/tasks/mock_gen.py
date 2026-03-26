"""Mock Paper Generation Celery Task.

Celery task wrapper around SmartMock.generate().
Decouples the heavyweight mock-paper generation (question selection +
PDF rendering + R2 upload) from the HTTP request/response cycle so the
student endpoint returns immediately with a task ID.

Workflow:
1. Student calls POST /student/mock/generate
2. The endpoint enqueues this task and returns {task_id, status: 'queued'}
3. Worker generates the mock paper asynchronously
4. Student can poll GET /student/mock/{mock_id} to check readiness
"""

import asyncio
from workers.celery_app import celery_app


async def _generate_mock_async(user_id: str, institution_id: str) -> dict:
    """Async SmartMock generation pipeline."""
    from engines.ape.smart_mock import smart_mock
    return await smart_mock.generate(user_id=user_id, institution_id=institution_id)


@celery_app.task(name="generate_mock_paper", bind=True, max_retries=2)
def generate_mock_paper(self, user_id: str, institution_id: str):
    """Celery task: generate a personalised SmartMock exam paper.

    Selects questions from the student's question bank, overweighting
    weak topics (2× probability), renders a PDF, uploads to R2, and
    creates a mock record in Supabase.

    Args:
        user_id: Student's UUID.
        institution_id: Institution slug.

    Returns:
        {mock_id, pdf_url}
    """
    try:
        result = asyncio.run(_generate_mock_async(user_id, institution_id))
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
