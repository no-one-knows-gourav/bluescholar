"""Readiness Score Engine — Section 9 of prototype.md.

Computes a 0-100 readiness score for a student using four weighted signals:

  score = mock_avg      * 0.40
        + gap_coverage  * 0.25
        + consistency   * 0.20
        + coverage      * 0.15
        - urgency_penalty

Components:
- mock_avg       : average of last 3 mock percentages
- gap_coverage   : fraction of weak spots that have improved to ≥ 70
- consistency    : days_active / days_since_signup (capped at 1.0)
- coverage       : fraction of syllabus topics covered by uploaded notes
- urgency_penalty: increases as exam date approaches (max 20 pts)
"""

from datetime import date, datetime, timezone
from core.vector import qdrant
from core.embeddings import embeddings


class ReadinessEngine:
    """Computes the student readiness score from live Supabase + Qdrant data."""

    async def compute(self, user_id: str, institution_id: str) -> dict:
        """Return the readiness score and its four component values.

        Returns:
            {score, mock_component, gap_component, consistency_component,
             coverage_component, days_to_exam}
        """
        mock_avg = await self._mock_avg(user_id)
        gap_coverage = await self._gap_coverage(user_id)
        consistency = await self._consistency(user_id)
        syllabus_coverage = await self._syllabus_coverage(user_id, institution_id)
        days_to_exam = await self._days_to_exam(user_id)

        # Section 9 urgency penalty
        urgency_penalty = max(0, (10 - days_to_exam) * 2) if days_to_exam < 10 else 0

        raw = (
            mock_avg * 0.40
            + (gap_coverage * 100) * 0.25
            + (consistency * 100) * 0.20
            + (syllabus_coverage * 100) * 0.15
        ) - urgency_penalty

        score = max(0.0, min(100.0, round(raw, 1)))

        return {
            "score": score,
            "mock_component": round(mock_avg * 0.40, 2),
            "gap_component": round(gap_coverage * 100 * 0.25, 2),
            "consistency_component": round(consistency * 100 * 0.20, 2),
            "coverage_component": round(syllabus_coverage * 100 * 0.15, 2),
            "days_to_exam": days_to_exam,
        }

    # ── Components ────────────────────────────────────────────────────────

    async def _mock_avg(self, user_id: str) -> float:
        """Average of the last 3 mock score percentages."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("mock_results")
                .select("score, max_score")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(9)   # last ~3 mocks × 3 topics each
                .execute()
            )
            data = rows.data or []
            if not data:
                return 0.0
            pcts = [
                (r["score"] / r["max_score"] * 100)
                for r in data
                if r.get("max_score") and r["max_score"] > 0
            ]
            # Average of last 3 mock percentages
            return sum(pcts[:3]) / len(pcts[:3]) if pcts else 0.0
        except Exception:
            return 0.0

    async def _gap_coverage(self, user_id: str) -> float:
        """Fraction of weak spots that have improved to score ≥ 70."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("weak_spots")
                .select("score")
                .eq("user_id", user_id)
                .execute()
            )
            data = rows.data or []
            if not data:
                return 1.0  # no gaps = fully covered
            improved = sum(1 for r in data if r.get("score", 0) >= 70)
            return improved / len(data)
        except Exception:
            return 0.0

    async def _consistency(self, user_id: str) -> float:
        """days_active / days_since_signup, capped at 1.0."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

            # Get signup date
            profile = (
                sb.table("profiles")
                .select("created_at")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            if not profile.data:
                return 0.0

            signup_str = profile.data[0].get("created_at", "")
            signup_dt = datetime.fromisoformat(signup_str.replace("Z", "+00:00"))
            days_since_signup = max(1, (datetime.now(timezone.utc) - signup_dt).days)

            # Count distinct active days from chat_history + revision_todos
            history = (
                sb.table("chat_history")
                .select("created_at")
                .eq("user_id", user_id)
                .execute()
            )
            todos = (
                sb.table("revision_todos")
                .select("updated_at, status")
                .eq("user_id", user_id)
                .eq("status", "done")
                .execute()
            )

            active_days = set()
            for row in (history.data or []):
                dt_str = row.get("created_at", "")
                if dt_str:
                    active_days.add(dt_str[:10])
            for row in (todos.data or []):
                dt_str = row.get("updated_at", "")
                if dt_str:
                    active_days.add(dt_str[:10])

            return min(1.0, len(active_days) / days_since_signup)
        except Exception:
            return 0.0

    async def _syllabus_coverage(self, user_id: str, institution_id: str) -> float:
        """Fraction of syllabus topics that have matching notes in Qdrant."""
        try:
            from engines.ace.syllabus_mapper import syllabus_mapper
            syllabus = await syllabus_mapper.get_syllabus(institution_id)
            if not syllabus:
                return 0.0

            units = syllabus.get("units", [])
            all_topics = [
                t.get("name", "")
                for u in units
                for t in u.get("topics", [])
                if t.get("name")
            ]
            if not all_topics:
                return 0.0

            covered = 0
            collection = f"{institution_id}_{user_id}_notes"
            for topic in all_topics:
                try:
                    vec = await embeddings.embed(topic)
                    hits = await qdrant.search(
                        collection=collection,
                        query=vec,
                        limit=1,
                        score_threshold=0.65,
                    )
                    if hits:
                        covered += 1
                except Exception:
                    pass

            return covered / len(all_topics)
        except Exception:
            return 0.0

    async def _days_to_exam(self, user_id: str) -> int:
        """Days until the student's next exam from revision_schedules."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            row = (
                sb.table("revision_schedules")
                .select("exam_date")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if row.data and row.data[0].get("exam_date"):
                exam_date = date.fromisoformat(row.data[0]["exam_date"])
                return max(0, (exam_date - date.today()).days)
        except Exception:
            pass
        return 999  # no exam set → no urgency penalty


# Singleton
readiness_engine = ReadinessEngine()
