"""GapFinder — Teaching Gap Detector.

Cross-references the institution's syllabus topics against:
- Qdrant ``{institution_id}_courseware`` — what was taught
- Qdrant ``{institution_id}_exams``      — what was examined

Classifies each gap:
- ``coverage_gap``  — examined but not in courseware
- ``performance_gap`` — taught but avg mock score < 50
- ``blind_spot``    — on syllabus, never taught or examined

Used by the faculty dashboard to identify teaching and curriculum deficiencies.
"""

from core.vector import qdrant
from core.embeddings import embeddings


class GapFinder:
    """Detects teaching and examination gaps in the institution's syllabus."""

    async def analyze(self, institution_id: str) -> dict:
        """Run the full gap analysis for an institution.

        Returns:
            {gaps: list[gap_dict], total_topics: int}
        """
        syllabus = await self._get_syllabus(institution_id)
        if not syllabus:
            return {"gaps": [], "total_topics": 0, "error": "No syllabus found."}

        units = syllabus.get("units", [])
        total_topics = sum(len(u.get("topics", [])) for u in units)

        gaps: list[dict] = []

        for unit in units:
            unit_number = unit.get("unit_number")
            weightage = unit.get("weightage_marks", 0)

            for topic in unit.get("topics", []):
                topic_name = topic.get("name", "")
                if not topic_name:
                    continue

                topic_vec = await embeddings.embed(topic_name)

                # Search courseware coverage
                courseware_hits = await self._search(
                    f"{institution_id}_courseware", topic_vec
                )

                # Search exam coverage
                exam_hits = await self._search(
                    f"{institution_id}_exams", topic_vec
                )

                # Avg mock score for this topic
                avg_mock = await self._avg_mock_score(institution_id, topic_name)

                # Classify
                gap_type = self._classify(courseware_hits, exam_hits, avg_mock)

                if gap_type:
                    gaps.append({
                        "topic": topic_name,
                        "unit": unit_number,
                        "gap_type": gap_type,
                        "weightage": weightage,
                        "avg_mock_score": avg_mock,
                        "courseware_coverage": len(courseware_hits),
                        "exam_frequency": len(exam_hits),
                    })

        return {"gaps": gaps, "total_topics": total_topics}

    # ── Classification ────────────────────────────────────────────────────

    @staticmethod
    def _classify(
        courseware_hits: list,
        exam_hits: list,
        avg_mock: float | None,
    ) -> str | None:
        if not courseware_hits and exam_hits:
            return "coverage_gap"       # Examined but not taught
        if courseware_hits and avg_mock is not None and avg_mock < 50:
            return "performance_gap"    # Taught but students fail
        if not courseware_hits and not exam_hits:
            return "blind_spot"         # On syllabus, never seen
        return None

    # ── Data fetchers ─────────────────────────────────────────────────────

    async def _get_syllabus(self, institution_id: str) -> dict | None:
        from engines.ace.syllabus_mapper import syllabus_mapper
        return await syllabus_mapper.get_syllabus(institution_id)

    async def _search(self, collection: str, query: list[float]) -> list:
        try:
            return await qdrant.search(
                collection=collection,
                query=query,
                limit=3,
                score_threshold=0.65,
            )
        except Exception:
            return []

    async def _avg_mock_score(
        self, institution_id: str, topic: str
    ) -> float | None:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("mock_results")
                .select("score, max_score")
                .eq("institution_id", institution_id)
                .eq("topic", topic)
                .execute()
            )
            data = rows.data or []
            if not data:
                return None
            scores = [
                (r["score"] / r["max_score"] * 100)
                for r in data
                if r.get("max_score")
            ]
            return round(sum(scores) / len(scores), 1) if scores else None
        except Exception:
            return None


# Singleton
gap_finder = GapFinder()
