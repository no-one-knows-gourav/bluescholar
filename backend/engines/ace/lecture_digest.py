"""LectureDigest — Lecture/Document Summariser.

Generates structured summaries of uploaded documents by pulling
chunks from Qdrant and running them through a cost-efficient LLM.
"""

import json
from core.llm import llm
from core.vector import qdrant

DIGEST_PROMPT = """\
You are LectureDigest, an academic summarisation engine.
Given chunks of a lecture document, produce a structured summary as JSON:

{
  "title": "Inferred title / topic of the document",
  "summary": "2-3 paragraph overview of the entire document content",
  "key_concepts": [
    {"concept": "...", "explanation": "1-2 sentence explanation"}
  ],
  "definitions": [
    {"term": "...", "definition": "..."}
  ],
  "formulas": [
    {"name": "...", "formula": "...", "context": "when/why it is used"}
  ],
  "review_questions": [
    "Question that tests understanding of the material"
  ]
}

Rules:
1. Extract ALL key concepts, not just the first few.
2. Include formulas/equations only if present in the source text.
3. Generate 3-5 review questions that test different Bloom's levels.
4. If the document is non-technical, omit the "formulas" array.
5. Return ONLY valid JSON. No preamble or explanation outside the JSON.
"""


class LectureDigest:
    """Summarises uploaded lecture documents into structured study aids."""

    async def digest(
        self,
        doc_id: str,
        user_id: str,
        institution_id: str,
    ) -> dict:
        """Generate a structured digest for a specific document.

        Args:
            doc_id: The document ID to summarise.
            user_id: The student's user ID.
            institution_id: Institution slug for collection namespacing.

        Returns:
            Structured summary dict with key_concepts, definitions,
            formulas, and review_questions.
        """
        # 1. Pull document chunks from Qdrant
        chunks = await self._get_document_chunks(doc_id, user_id, institution_id)

        if not chunks:
            return {
                "error": "No processed content found for this document. It may still be processing.",
                "title": "Unknown",
                "summary": "",
                "key_concepts": [],
                "definitions": [],
                "formulas": [],
                "review_questions": [],
            }

        # 2. Combine chunks into a single text (up to 6000 chars for Haiku)
        combined_text = "\n\n".join(
            c.payload.get("text", "") for c in chunks
        )[:6000]

        # 3. Generate digest via Haiku (cost-efficient for single-doc tasks)
        response = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system=DIGEST_PROMPT,
            user=combined_text,
            max_tokens=2048,
            temperature=0.2,
        )

        # 4. Parse response
        try:
            digest = json.loads(response.text)
        except json.JSONDecodeError:
            # If JSON parsing fails, wrap the raw text
            digest = {
                "title": "Lecture Summary",
                "summary": response.text,
                "key_concepts": [],
                "definitions": [],
                "formulas": [],
                "review_questions": [],
            }

        return digest

    async def digest_from_text(self, text: str, filename: str = "") -> dict:
        """Generate a digest from raw text (no Qdrant lookup).

        Useful for on-the-fly summarisation of pasted text or
        documents not yet fully processed.
        """
        response = await llm.complete(
            model="claude-haiku-4-5-20251001",
            system=DIGEST_PROMPT,
            user=text[:6000],
            max_tokens=2048,
            temperature=0.2,
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "title": filename or "Summary",
                "summary": response.text,
                "key_concepts": [],
                "definitions": [],
                "formulas": [],
                "review_questions": [],
            }

    async def _get_document_chunks(
        self,
        doc_id: str,
        user_id: str,
        institution_id: str,
    ) -> list:
        """Retrieve all chunks for a specific document from Qdrant."""
        try:
            return await qdrant.scroll(
                collection=f"{institution_id}_{user_id}_notes",
                limit=50,
                filters={"doc_id": doc_id},
            )
        except Exception:
            return []


# Singleton
lecture_digest = LectureDigest()
