"""DocDoubt — Strict Grounding Q&A Engine.

Answers student questions ONLY from their uploaded course material.
Uses RAG: embed question → search Qdrant → build context → stream LLM response.
Citations are inline [Source: filename, Page X].
"""

import json
from typing import AsyncGenerator
from core.llm import llm
from core.vector import qdrant
from core.embeddings import embeddings

SYSTEM_PROMPT = """\
You are DocDoubt, a strictly grounded academic assistant for {student_name}.
You ONLY answer questions using the provided context passages from the student's uploaded course material.

Rules:
1. If the answer is in the context: answer clearly, then cite the source as [Source: {filename}, Page {page}]
2. If partially covered: answer what you can, then say "⚠ Partial coverage — the following aspect is not in your uploaded material: [gap]"
3. If not covered at all: say exactly "✗ This question falls outside your uploaded course material. Consider checking [topic area] in your textbook."
4. NEVER generate information that is not directly supported by the provided context.
5. Keep answers concise and well-structured. Use bullet points for multi-part answers.
6. When citing, always include the source filename and page number if available.
"""

NO_RESULTS_MSG = "✗ This question falls outside your uploaded course material. Upload more notes or course materials to expand my knowledge base."


class DocDoubt:
    """RAG-grounded Q&A chat engine for student uploaded materials."""

    SCORE_THRESHOLD = 0.60
    MAX_RESULTS_PER_COLLECTION = 5

    async def chat(
        self,
        question: str,
        user_id: str,
        institution_id: str,
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a grounded answer to the student's question.

        Searches both student notes and faculty courseware, builds
        context with citations, then streams the LLM response.

        Yields:
            Text chunks of the streamed response.
        """
        # 1. Embed the question
        q_embedding = await embeddings.embed(question)

        # 2. Search student notes AND faculty courseware
        student_results = await self._safe_search(
            collection=f"{institution_id}_{user_id}_notes",
            query=q_embedding,
        )
        faculty_results = await self._safe_search(
            collection=f"{institution_id}_courseware",
            query=q_embedding,
        )

        all_results = student_results + faculty_results

        # 3. If nothing found, yield the no-results message
        if not all_results:
            yield NO_RESULTS_MSG
            return

        # Sort by relevance score descending, take top 8
        all_results.sort(key=lambda r: r.score, reverse=True)
        top_results = all_results[:8]

        # 4. Build context with citations
        context = self._build_context(top_results)

        # 5. Build messages
        system = SYSTEM_PROMPT.format(
            student_name="Student",
            filename="{filename}",
            page="{page}",
        )

        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        })

        # 6. Stream response
        async for chunk in llm.stream(
            model="claude-sonnet-4-20250514",
            system=system,
            messages=messages,
        ):
            yield chunk

    async def get_sources(
        self,
        question: str,
        user_id: str,
        institution_id: str,
    ) -> list[dict]:
        """Return source citations for a question without generating a response.

        Useful for the frontend to display source documents alongside the chat.
        """
        q_embedding = await embeddings.embed(question)

        student_results = await self._safe_search(
            collection=f"{institution_id}_{user_id}_notes",
            query=q_embedding,
        )
        faculty_results = await self._safe_search(
            collection=f"{institution_id}_courseware",
            query=q_embedding,
        )

        all_results = student_results + faculty_results
        all_results.sort(key=lambda r: r.score, reverse=True)

        return [
            {
                "filename": r.payload.get("filename", "Unknown"),
                "page": r.payload.get("page_number", r.payload.get("page", None)),
                "score": round(r.score, 3),
                "text_preview": r.payload.get("text", "")[:200],
                "source_type": r.payload.get("doc_type", "note"),
            }
            for r in all_results[:8]
        ]

    def _build_context(self, results: list) -> str:
        """Build a formatted context string from search results."""
        sections = []
        for r in results:
            filename = r.payload.get("filename", "Unknown")
            page = r.payload.get("page_number", r.payload.get("page", "?"))
            text = r.payload.get("text", "")
            sections.append(
                f"[Source: {filename}, Page {page}]\n{text}"
            )
        return "\n\n---\n\n".join(sections)

    async def _safe_search(
        self,
        collection: str,
        query: list[float],
    ) -> list:
        """Search a collection, returning empty list if collection doesn't exist."""
        try:
            return await qdrant.search(
                collection=collection,
                query=query,
                limit=self.MAX_RESULTS_PER_COLLECTION,
                score_threshold=self.SCORE_THRESHOLD,
            )
        except Exception:
            return []


# Singleton
doc_doubt = DocDoubt()
