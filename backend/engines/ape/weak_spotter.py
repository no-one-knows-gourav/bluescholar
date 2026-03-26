"""WeakSpotter — Concept Gap Tracker.

Tracks which concepts a student struggles with by aggregating signals from:
- Mock exam results (per-topic scores)
- MemoryTutor chat sessions (struggle flags)

Stores and retrieves ``weak_spots`` rows in Supabase.
Score: 0–100 where lower = weaker. Updated via exponential moving average.
"""

from datetime import datetime, timezone


class WeakSpotter:
    """Maintains and exposes the student's weak concept map."""

    # Exponential moving average factor — new score weight vs historical
    EMA_ALPHA = 0.4

    async def get_weak_spots(self, user_id: str) -> list[dict]:
        """Return all weak spots for a student, ordered weakest first.

        Returns:
            List of dicts: {concept, unit, score, attempt_count, last_updated}
        """
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("weak_spots")
                .select("*")
                .eq("user_id", user_id)
                .order("score", desc=False)
                .execute()
            )
            return rows.data or []
        except Exception:
            return []

    async def update_from_chat(
        self,
        user_id: str,
        concept: str,
        unit: int | None,
        struggled: bool,
    ) -> None:
        """Signal from a tutor session that a student found a concept hard/easy.

        A struggle nudges the score down; a success nudges it up.

        Args:
            user_id: Student ID.
            concept: Topic that was discussed.
            unit: Syllabus unit number if known.
            struggled: True = student found it hard, False = understood it.
        """
        signal_score = 30.0 if struggled else 85.0
        await self._upsert_score(user_id, concept, unit, signal_score)

    async def update_from_mock(
        self,
        user_id: str,
        topic_results: list[dict],
    ) -> None:
        """Batch-update scores from a completed mock exam.

        Args:
            topic_results: List of {topic, unit, score, max_score} dicts.
        """
        for result in topic_results:
            topic = result.get("topic")
            if not topic:
                continue
            max_score = result.get("max_score", 10)
            raw_score = result.get("score", 0)
            normalised = (raw_score / max_score * 100) if max_score else 0
            await self._upsert_score(
                user_id,
                topic,
                result.get("unit"),
                normalised,
            )

    # ── Private helpers ───────────────────────────────────────────────────

    async def _upsert_score(
        self,
        user_id: str,
        concept: str,
        unit: int | None,
        new_score: float,
    ) -> None:
        """Insert or update a weak_spots row using an EMA for the score."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

            # Check for existing row
            existing = (
                sb.table("weak_spots")
                .select("id, score, attempt_count")
                .eq("user_id", user_id)
                .eq("concept", concept)
                .limit(1)
                .execute()
            )

            now = datetime.now(timezone.utc).isoformat()

            if existing.data:
                row = existing.data[0]
                old_score = row.get("score", new_score)
                blended = (1 - self.EMA_ALPHA) * old_score + self.EMA_ALPHA * new_score
                (
                    sb.table("weak_spots")
                    .update({
                        "score": round(blended, 2),
                        "attempt_count": row.get("attempt_count", 0) + 1,
                        "last_updated": now,
                    })
                    .eq("id", row["id"])
                    .execute()
                )
            else:
                sb.table("weak_spots").insert({
                    "user_id": user_id,
                    "concept": concept,
                    "unit": unit,
                    "score": round(new_score, 2),
                    "attempt_count": 1,
                    "last_updated": now,
                }).execute()
        except Exception:
            pass


# Singleton
weak_spotter = WeakSpotter()
