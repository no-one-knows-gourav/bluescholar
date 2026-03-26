"""Exam Difficulty Calibrator — Bloom's level distribution analyser.

Analyses a set of questions (from the question bank or a specific exam)
and returns:
- difficulty_score (0–10): weighted by Bloom's level complexity
- bloom_distribution: percentage breakdown across all 6 Bloom's levels
- recommended_adjustments: LLM-generated plain-English suggestions

Bloom's level complexity weights (higher = harder):
  remember → 1, understand → 2, apply → 3,
  analyze → 4, evaluate → 5, create → 6
"""

import json
from core.llm import llm


BLOOM_WEIGHTS = {
    "remember": 1,
    "understand": 2,
    "apply": 3,
    "analyze": 4,
    "evaluate": 5,
    "create": 6,
}

CALIBRATOR_PROMPT = """\
You are an academic exam design expert. Analyse the following exam Bloom's taxonomy distribution
and question difficulty data. Provide practical, concise recommendations for the faculty.

Data:
- Difficulty score: {score}/10
- Bloom's distribution: {distribution}
- Total questions: {total}

Guidelines: A well-balanced exam (university level) should have:
- 20% remember/understand (easy recall)
- 40% apply/analyze (core skills)
- 40% evaluate/create (higher order thinking)

Return a JSON array of 3-5 short recommendations (plain English, 1-2 sentences each):
["recommendation 1", "recommendation 2", ...]
"""


class DifficultyCalibrator:
    """Analyses question bank Bloom's distribution and calibrates exam difficulty."""

    async def calibrate(
        self,
        institution_id: str,
        exam_id: str | None = None,
    ) -> dict:
        """Run difficulty calibration.

        Args:
            institution_id: Used to scope question_bank queries.
            exam_id: Optional. If provided, only analyses questions mapped to this exam.

        Returns:
            {difficulty_score, bloom_distribution, total_questions, recommended_adjustments}
        """
        questions = await self._load_questions(institution_id, exam_id)
        if not questions:
            return {
                "difficulty_score": 0.0,
                "bloom_distribution": {},
                "total_questions": 0,
                "recommended_adjustments": ["No questions found in the bank yet."],
            }

        # Bloom's distribution
        bloom_counts: dict[str, int] = {k: 0 for k in BLOOM_WEIGHTS}
        for q in questions:
            level = (q.get("bloom_level") or "remember").lower()
            if level in bloom_counts:
                bloom_counts[level] += 1

        total = len(questions)
        bloom_distribution = {
            level: round(count / total * 100, 1)
            for level, count in bloom_counts.items()
        }

        # Weighted difficulty score (1–10 scale)
        weighted_sum = sum(
            BLOOM_WEIGHTS.get(level, 1) * count
            for level, count in bloom_counts.items()
        )
        max_possible = BLOOM_WEIGHTS["create"] * total  # all at highest
        min_possible = BLOOM_WEIGHTS["remember"] * total  # all at lowest
        if max_possible > min_possible:
            raw = (weighted_sum - min_possible) / (max_possible - min_possible) * 10
        else:
            raw = 0.0
        difficulty_score = round(raw, 2)

        # LLM recommendations
        recommendations = await self._get_recommendations(
            difficulty_score, bloom_distribution, total
        )

        return {
            "difficulty_score": difficulty_score,
            "bloom_distribution": bloom_distribution,
            "total_questions": total,
            "recommended_adjustments": recommendations,
        }

    # ── Private helpers ───────────────────────────────────────────────────

    async def _load_questions(
        self, institution_id: str, exam_id: str | None
    ) -> list[dict]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

            if exam_id:
                # Load questions mapped to this specific exam
                mapping = (
                    sb.table("exam_questions_map")
                    .select("question_id")
                    .eq("exam_id", exam_id)
                    .execute()
                )
                q_ids = [r["question_id"] for r in (mapping.data or [])]
                if not q_ids:
                    return []
                rows = (
                    sb.table("question_bank")
                    .select("bloom_level, marks")
                    .in_("id", q_ids)
                    .execute()
                )
            else:
                rows = (
                    sb.table("question_bank")
                    .select("bloom_level, marks")
                    .eq("institution_id", institution_id)
                    .execute()
                )
            return rows.data or []
        except Exception:
            return []

    async def _get_recommendations(
        self,
        score: float,
        distribution: dict,
        total: int,
    ) -> list[str]:
        try:
            resp = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=CALIBRATOR_PROMPT.format(
                    score=score,
                    distribution=json.dumps(distribution),
                    total=total,
                ),
                user="Generate recommendations.",
                max_tokens=512,
                temperature=0.3,
            )
            return json.loads(resp.text)
        except Exception:
            return [
                f"Current difficulty score is {score}/10.",
                "Ensure a mix of Bloom's levels for a balanced assessment.",
            ]


# Singleton
difficulty_calibrator = DifficultyCalibrator()
