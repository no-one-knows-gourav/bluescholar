"""SyllabusMapper — Intelligent Syllabus Parser.

Uses LLM to extract structured syllabus data from uploaded PDFs,
then embeds each topic into Qdrant for downstream matching
(ChaosCleaner coverage, PaperPatternMiner, SmartMock, etc.).
"""

import json
from uuid import uuid4
from core.llm import llm
from core.vector import qdrant
from core.embeddings import embeddings

SYLLABUS_PARSE_PROMPT = """
You are parsing a university syllabus PDF. Extract a structured JSON with this schema:
{
  "units": [
    {
      "unit_number": 1,
      "title": "...",
      "weightage_marks": 20,
      "topics": [
        {"name": "...", "subtopics": ["...", "..."], "prerequisite_topics": ["..."]}
      ]
    }
  ],
  "total_marks": 100,
  "exam_duration_hours": 3
}
Return ONLY valid JSON. No preamble.
"""


class SyllabusMapper:
    """Parses syllabus text into structured data and indexes topics for retrieval."""

    async def parse(self, syllabus_text: str, institution_id: str) -> dict:
        """Parse syllabus text into structured JSON and embed topics.

        Args:
            syllabus_text: Raw text extracted from the syllabus PDF.
            institution_id: Institution slug for Qdrant namespacing.

        Returns:
            Parsed syllabus dict with units/topics/weightage.
        """
        # 1. LLM extraction — use Haiku for cost efficiency on single-doc tasks
        response = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system=SYLLABUS_PARSE_PROMPT,
            user=syllabus_text[:8000],  # First 8k chars covers most syllabi
        )
        parsed = json.loads(response.text)

        # 2. Embed each topic and upsert to Qdrant syllabus collection
        collection = f"{institution_id}_syllabus"
        for unit in parsed.get("units", []):
            for topic in unit.get("topics", []):
                topic_text = topic["name"]
                if topic.get("subtopics"):
                    topic_text += " " + " ".join(topic["subtopics"])

                embedding = await embeddings.embed(topic_text)
                await qdrant.upsert(
                    collection=collection,
                    vector=embedding,
                    payload={
                        "unit": unit["unit_number"],
                        "unit_title": unit.get("title", ""),
                        "topic": topic["name"],
                        "subtopics": topic.get("subtopics", []),
                        "prerequisites": topic.get("prerequisite_topics", []),
                        "weightage": unit.get("weightage_marks", 0),
                        "institution_id": institution_id,
                    },
                    point_id=str(uuid4()),
                )

        return parsed

    async def get_syllabus(self, institution_id: str) -> dict | None:
        """Retrieve the parsed syllabus for an institution.

        Reconstructs from Qdrant syllabus collection.
        In production, this would query Supabase 'syllabi' table.
        """
        try:
            points = await qdrant.scroll(
                collection=f"{institution_id}_syllabus",
                limit=200,
            )
            if not points:
                return None

            # Reconstruct unit structure from flat points
            units_map: dict[int, dict] = {}
            for p in points:
                unit_num = p.payload.get("unit", 0)
                if unit_num not in units_map:
                    units_map[unit_num] = {
                        "unit_number": unit_num,
                        "title": p.payload.get("unit_title", ""),
                        "weightage_marks": p.payload.get("weightage", 0),
                        "topics": [],
                    }
                units_map[unit_num]["topics"].append({
                    "name": p.payload.get("topic", ""),
                    "subtopics": p.payload.get("subtopics", []),
                    "prerequisite_topics": p.payload.get("prerequisites", []),
                })

            return {
                "units": sorted(units_map.values(), key=lambda u: u["unit_number"]),
            }
        except Exception:
            return None


# Singleton
syllabus_mapper = SyllabusMapper()
