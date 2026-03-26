"""StudyTimePredictor — Peak Study Window Detector.

Analyses the student's historical activity timestamps (chat sessions,
completed revision tasks) and returns their typical peak study hours.

Used by RevisionClock.generate() to assign difficult topics to peak windows
and lighter revision to off-peak hours.

Output: ranked list of hour buckets (0-23) by historical activity count.
"""

from datetime import datetime, timezone


class StudyTimePredictor:
    """Predicts the student's peak study windows from historical activity."""

    async def predict(self, user_id: str) -> dict:
        """Return hourly activity distribution and recommended peak windows.

        Returns:
            {
                "hour_distribution": {0: count, 1: count, ..., 23: count},
                "peak_hours": [h1, h2, h3],      # top 3 hours
                "peak_windows": ["morning", "afternoon", "evening", "night"],
                "data_points": int               # total activity records analysed
            }
        """
        hour_distribution = await self._build_distribution(user_id)
        total = sum(hour_distribution.values())

        if total == 0:
            # No data — return a sensible academic default
            return {
                "hour_distribution": {h: 0 for h in range(24)},
                "peak_hours": [10, 15, 20],
                "peak_windows": ["morning", "evening"],
                "data_points": 0,
            }

        # Top 3 most active hours
        sorted_hours = sorted(hour_distribution, key=hour_distribution.get, reverse=True)
        peak_hours = sorted_hours[:3]

        # Map to named windows
        windows = set()
        for h in peak_hours:
            if 5 <= h < 12:
                windows.add("morning")
            elif 12 <= h < 17:
                windows.add("afternoon")
            elif 17 <= h < 21:
                windows.add("evening")
            else:
                windows.add("night")

        return {
            "hour_distribution": hour_distribution,
            "peak_hours": peak_hours,
            "peak_windows": sorted(windows),
            "data_points": total,
        }

    # ── Private helpers ────────────────────────────────────────────────────

    async def _build_distribution(self, user_id: str) -> dict[int, int]:
        """Aggregate activity counts per hour from Supabase tables."""
        dist: dict[int, int] = {h: 0 for h in range(24)}

        try:
            from config import get_settings
            from supabase import create_client

            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

            # Source 1: chat_history (DocDoubt + MemoryTutor sessions)
            chat_rows = (
                sb.table("chat_history")
                .select("created_at")
                .eq("user_id", user_id)
                .execute()
            )
            for row in (chat_rows.data or []):
                h = self._extract_hour(row.get("created_at", ""))
                if h is not None:
                    dist[h] += 1

            # Source 2: revision_todos completed timestamps
            todo_rows = (
                sb.table("revision_todos")
                .select("updated_at")
                .eq("user_id", user_id)
                .eq("status", "done")
                .execute()
            )
            for row in (todo_rows.data or []):
                h = self._extract_hour(row.get("updated_at", ""))
                if h is not None:
                    dist[h] += 1

            # Source 3: mock submissions
            mock_rows = (
                sb.table("mocks")
                .select("completed_at")
                .eq("user_id", user_id)
                .not_.is_("completed_at", "null")
                .execute()
            )
            for row in (mock_rows.data or []):
                h = self._extract_hour(row.get("completed_at", ""))
                if h is not None:
                    dist[h] += 1

        except Exception:
            pass

        return dist

    @staticmethod
    def _extract_hour(dt_str: str) -> int | None:
        """Parse an ISO timestamp and return the UTC hour (0-23)."""
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.hour
        except Exception:
            return None


# Singleton
study_time_predictor = StudyTimePredictor()
