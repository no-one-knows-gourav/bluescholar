"""PlagueScope — Submission Similarity Analyser.

Embeds all exam submissions, computes a pairwise cosine similarity matrix,
and flags student pairs whose cosine similarity exceeds 0.85.

Used by faculty to detect potential collusion or plagiarism.
"""

import math
from core.embeddings import embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


PLAGIARISM_THRESHOLD = 0.85


class PlagueScope:
    """Computes pairwise similarity across exam submissions."""

    async def analyze_batch(self, exam_id: str, institution_id: str) -> dict:
        """Run plagiarism analysis for all final submissions of an exam.

        Args:
            exam_id: The exam to analyse.
            institution_id: Institution slug (for context, not used in query).

        Returns:
            {student_ids, matrix, flagged_pairs, threshold}
        """
        # 1. Load submissions
        submissions = await self._load_submissions(exam_id)
        if len(submissions) < 2:
            return {
                "student_ids": [s["student_id"] for s in submissions],
                "matrix": [[1.0]],
                "flagged_pairs": [],
                "threshold": PLAGIARISM_THRESHOLD,
            }

        # 2. Embed each submission (concatenate all answers)
        student_ids: list[str] = []
        vectors: list[list[float]] = []
        for sub in submissions:
            sid = sub.get("student_id", "")
            answers = sub.get("answers") or {}
            combined = " ".join(str(v) for v in answers.values())[:8000]
            vec = await embeddings.embed(combined)
            student_ids.append(sid)
            vectors.append(vec)

        # 3. Compute pairwise cosine similarity matrix
        n = len(student_ids)
        matrix: list[list[float]] = []
        for i in range(n):
            row: list[float] = []
            for j in range(n):
                if i == j:
                    row.append(1.0)
                else:
                    sim = _cosine_similarity(vectors[i], vectors[j])
                    row.append(round(sim, 3))
            matrix.append(row)

        # 4. Flag pairs above threshold
        flagged_pairs: list[dict] = []
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i][j] > PLAGIARISM_THRESHOLD:
                    flagged_pairs.append({
                        "student_a": student_ids[i],
                        "student_b": student_ids[j],
                        "similarity": matrix[i][j],
                    })

        return {
            "student_ids": student_ids,
            "matrix": matrix,
            "flagged_pairs": flagged_pairs,
            "threshold": PLAGIARISM_THRESHOLD,
        }

    # ── Private helpers ───────────────────────────────────────────────────

    async def _load_submissions(self, exam_id: str) -> list[dict]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("exam_submissions")
                .select("student_id, answers")
                .eq("exam_id", exam_id)
                .execute()
            )
            return rows.data or []
        except Exception:
            return []


# Singleton
plague_scope = PlagueScope()
