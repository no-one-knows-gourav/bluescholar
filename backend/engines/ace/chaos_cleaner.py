"""ChaosCleaner — Note Chaos Organiser.

Handles document ingestion, processing, and syllabus coverage analysis
for student-uploaded notes (PDF, DOCX, PPTX, images, TXT).
"""

import json
from core.storage import storage
from core.vector import qdrant
from core.embeddings import embeddings


class ChaosCleaner:
    """Ingests student documents, queues processing, and computes syllabus coverage."""

    async def ingest(self, files: list[dict], user_id: str, institution_id: str) -> list[dict]:
        """Upload files to R2 and queue processing tasks.

        Args:
            files: List of dicts with 'filename', 'content' (bytes), 'content_type'.
            user_id: The uploading student's ID.
            institution_id: The institution slug.

        Returns:
            List of created document records.
        """
        from workers.tasks.ingest import process_document

        records = []
        for file in files:
            # 1. Upload raw file to R2
            key = f"uploads/{institution_id}/{user_id}/{file['filename']}"
            await storage.upload(key, file["content"], file.get("content_type", "application/octet-stream"))

            # 2. Queue Celery processing task
            process_document.delay(
                file_key=key,
                user_id=user_id,
                institution_id=institution_id,
                doc_type="student_note",
            )

            records.append({
                "user_id": user_id,
                "institution_id": institution_id,
                "r2_key": key,
                "filename": file["filename"],
                "status": "processing",
                "doc_type": "student_note",
            })

        return records

    async def get_coverage(self, user_id: str, institution_id: str) -> dict:
        """Cross-reference user's documents against syllabus topics.

        Returns a dict mapping topic names to coverage status:
        'covered', 'partial', or 'gap'.
        """
        syllabus_topics = await self._get_syllabus_topics(institution_id)
        if not syllabus_topics:
            return {"error": "No syllabus found for this institution."}

        coverage = {}
        for topic in syllabus_topics:
            topic_text = topic["name"]
            if topic.get("subtopics"):
                topic_text += " " + " ".join(topic["subtopics"])

            topic_embedding = await embeddings.embed(topic_text)

            results = await qdrant.search(
                collection=f"{institution_id}_{user_id}_notes",
                query=topic_embedding,
                limit=3,
                score_threshold=0.65,
            )

            if not results:
                coverage[topic["name"]] = {
                    "status": "gap",
                    "unit": topic.get("unit"),
                    "match_count": 0,
                }
            elif len(results) >= 2 and results[0].score > 0.75:
                coverage[topic["name"]] = {
                    "status": "covered",
                    "unit": topic.get("unit"),
                    "match_count": len(results),
                    "top_score": round(results[0].score, 3),
                }
            else:
                coverage[topic["name"]] = {
                    "status": "partial",
                    "unit": topic.get("unit"),
                    "match_count": len(results),
                    "top_score": round(results[0].score, 3),
                }

        return coverage

    async def _get_syllabus_topics(self, institution_id: str) -> list[dict]:
        """Retrieve flattened syllabus topics from Qdrant metadata.

        In production this would query Supabase. For now, scrolls the
        syllabus collection and extracts topic payloads.
        """
        try:
            points = await qdrant.scroll(
                collection=f"{institution_id}_syllabus",
                limit=200,
            )
            return [
                {
                    "name": p.payload.get("topic", ""),
                    "unit": p.payload.get("unit"),
                    "subtopics": p.payload.get("subtopics", []),
                }
                for p in points
                if p.payload.get("topic")
            ]
        except Exception:
            return []


# Singleton
chaos_cleaner = ChaosCleaner()
