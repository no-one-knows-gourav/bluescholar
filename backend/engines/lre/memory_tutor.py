"""MemoryTutor — Persistent Agentic Tutor.

Maintains a running understanding of the student's knowledge gaps across
every session. Each chat opens with a briefing built from Supabase
``chat_history`` and ``weak_spots``, so the LLM always knows what was
covered last time and which concepts are still unresolved.
"""

from typing import AsyncGenerator
from core.llm import llm


TUTOR_SYSTEM = """\
You are MemoryTutor, a persistent academic tutor who remembers this student's entire learning journey.

{context}

Your behaviour:
1. Open every session by acknowledging an unresolved gap from the last session (if any).
2. Never re-explain concepts the student has already mastered.
3. When the student hesitates or answers incorrectly, log it mentally — you will revisit it next session.
4. End every response with a short "Next up: [concept]" to guide the student forward.
5. Ground all explanations in the student's own uploaded course material when possible.
6. Keep responses clear, concise, and conversational — this is a live study session.
"""

NO_HISTORY_CONTEXT = """\
Prior session summary:
- This appears to be the first session.
- No prior gaps or topics on record yet.
- Introduce yourself warmly and ask where they want to start.
"""


class MemoryTutor:
    """Streaming tutor with persistent session context built from Supabase."""

    async def chat(
        self,
        message: str,
        user_id: str,
        institution_id: str,
        conversation: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a tutor response that is aware of the student's full history.

        Args:
            message: The student's latest message.
            user_id: Used to fetch chat history and weak spots.
            institution_id: Institution slug (reserved for future RAG grounding).
            conversation: Prior messages in this UI session as [{'role','content'}].

        Yields:
            Text chunks from the streamed LLM response.
        """
        # 1. Build session context from Supabase
        context = await self.get_session_context(user_id)

        # 2. Compose system prompt
        system = TUTOR_SYSTEM.format(context=context)

        # 3. Build message history
        messages = list(conversation or [])
        messages.append({"role": "user", "content": message})

        # 4. Stream response
        async for chunk in llm.stream(
            model="claude-sonnet-4-20250514",
            system=system,
            messages=messages,
            max_tokens=2048,
            temperature=0.5,
        ):
            yield chunk

        # 5. Persist this exchange to chat_history (best-effort)
        await self._save_history(user_id, message)

    async def get_session_context(self, user_id: str) -> str:
        """Build a tutor briefing from prior chat history and weak spots."""
        history = await self._fetch_history(user_id)
        gaps = await self._fetch_weak_spots(user_id)

        if not history and not gaps:
            return NO_HISTORY_CONTEXT

        # Topics covered in past sessions
        topics_seen: set[str] = set()
        for h in history:
            tags = h.get("topic_tags")
            if isinstance(tags, list):
                topics_seen.update(tags)
            elif isinstance(tags, str) and tags:
                topics_seen.add(tags)

        last_date = history[0].get("created_at", "unknown") if history else "none"
        gap_list = ", ".join(g["concept"] for g in gaps[:5]) if gaps else "none yet"
        topics_list = ", ".join(sorted(topics_seen)[:10]) if topics_seen else "none yet"

        return (
            f"Prior session summary:\n"
            f"- Topics previously covered: {topics_list}\n"
            f"- Unresolved gaps (lowest scores): {gap_list}\n"
            f"- Last session: {last_date}\n"
        )

    # ── Private helpers ───────────────────────────────────────────────────

    async def _fetch_history(self, user_id: str) -> list[dict]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("chat_history")
                .select("topic_tags, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )
            return rows.data or []
        except Exception:
            return []

    async def _fetch_weak_spots(self, user_id: str) -> list[dict]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("weak_spots")
                .select("concept, score")
                .eq("user_id", user_id)
                .order("score", desc=False)
                .limit(20)
                .execute()
            )
            return rows.data or []
        except Exception:
            return []

    async def _save_history(self, user_id: str, question: str) -> None:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            sb.table("chat_history").insert({
                "user_id": user_id,
                "agent": "memory_tutor",
                "question": question,
            }).execute()
        except Exception:
            pass


# Singleton
memory_tutor = MemoryTutor()
