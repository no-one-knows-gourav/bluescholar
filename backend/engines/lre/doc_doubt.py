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

Be concise. Answer in under 150 words unless the question requires more detail.
Use bullet points only when listing 3+ distinct items.
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

        # 2. Check Semantic Cache
        try:
            cache_results = await qdrant.search(
                collection=f"{institution_id}_semantic_cache",
                query=q_embedding,
                limit=1,
                score_threshold=0.92,
            )
            if cache_results and cache_results[0].payload.get("answer"):
                yield cache_results[0].payload["answer"]
                return
        except Exception:
            pass

        # 3. Search student notes AND faculty courseware
        student_results = await self._safe_search(
            collection=f"{institution_id}_{user_id}_notes",
            query=q_embedding,
        )
        faculty_results = await self._safe_search(
            collection=f"{institution_id}_courseware",
            query=q_embedding,
        )

        all_results = student_results + faculty_results

        # 4. If nothing found, yield the no-results message
        if not all_results:
            yield NO_RESULTS_MSG
            return

        # Sort by relevance score descending, take top 8
        all_results.sort(key=lambda r: r.score, reverse=True)
        top_results = all_results[:8]

        # 5. Build context with citations
        context = self._build_context(top_results)

        # 5.5 LLMLingua Prompt Compression (Strategy 5)
        try:
            from llmlingua import PromptCompressor
            if not hasattr(self, "_compressor"):
                self._compressor = PromptCompressor(model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank")
            compressed: dict = self._compressor.compress_prompt(context, rate=0.33, force_tokens=["\n", "?", "[", "]"])
            context = compressed.get("compressed_prompt", context)
        except Exception:
            pass

        # 6. Build messages
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

        # 7. Prefill Assistant response
        prefill_text = "Based on your uploaded material: "
        messages.append({"role": "assistant", "content": prefill_text})
        yield prefill_text

        # 8. Stream response and capture for cache
        full_response = prefill_text
        async for chunk in llm.stream(
            model="claude-sonnet-4-20250514",
            system=system,
            messages=messages,
        ):
            full_response += chunk
            yield chunk

        # 9. Save to Semantic Cache
        try:
            await qdrant.upsert(
                collection=f"{institution_id}_semantic_cache",
                vector=q_embedding,
                payload={"question": question, "answer": full_response}
            )
        except Exception:
            pass

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
