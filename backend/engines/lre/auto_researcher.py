"""AutoResearcher — Multi-Agent Report Builder.

Five-stage pipeline, each stage streamed as an SSE event:
  Planner → Researcher → Writer → Editor → Presenter

The final output is a Markdown report + a slide outline, both saved to
Supabase ``research_reports`` and yielded as the final SSE payload.
"""

import json
import asyncio
from typing import AsyncGenerator
from core.llm import llm


# ── Stage prompts ──────────────────────────────────────────────────────────

PLANNER_PROMPT = """\
You are a report planner. Given a topic, output a JSON array of 5–7 sections.
Each section: {"title": "...", "description": "2-sentence description of what this section covers"}
Return ONLY valid JSON — no markdown fences, no preamble.
"""

RESEARCHER_PROMPT = """\
You are a research assistant. Given a report section title and description,
write 3–5 key facts, statistics, or arguments that should appear in this section.
Keep each point concise (1–2 sentences). Return as a plain bullet list.
"""

WRITER_PROMPT = """\
You are writing a section of a formal academic report.
Write 300–400 words for this section. Be specific. Use the research notes provided.
Use a formal, clear academic tone. No bullet points — full paragraphs only.
"""

EDITOR_PROMPT = """\
Edit this academic report draft. Fix transitions between sections, remove repetition,
ensure a consistent formal tone throughout, and improve flow.
Return the improved full report — preserve all section headings (##).
"""

PRESENTER_PROMPT = """\
Convert this academic report into a PowerPoint slide outline.
Format strictly as:
SLIDE 1: [Slide Title]
• Bullet point
• Bullet point

SLIDE 2: [Slide Title]
...

Maximum 6 slides. Each slide: 3–5 concise bullet points.
"""


class AutoResearcher:
    """5-stage multi-agent report builder with SSE progress streaming."""

    async def run(
        self, topic: str, user_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream SSE events through all 5 stages and yield the final report.

        Args:
            topic: The research topic entered by the student.
            user_id: Student's user ID for persisting the report.

        Yields:
            Server-Sent Events formatted strings.
        """
        def _sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        # ── Stage 1: Planner ────────────────────────────────────────────
        yield _sse({"stage": "planner", "status": "running"})
        sections = await self._plan(topic)
        yield _sse({
            "stage": "planner",
            "status": "done",
            "sections": [s.get("title", "") for s in sections],
        })

        # ── Stage 2: Researcher ─────────────────────────────────────────
        yield _sse({"stage": "researcher", "status": "running"})
        research_notes = await self._research(topic, sections)
        yield _sse({"stage": "researcher", "status": "done"})

        # ── Stage 3: Writer ─────────────────────────────────────────────
        yield _sse({"stage": "writer", "status": "running"})
        draft_sections = await self._write(sections, research_notes)
        yield _sse({"stage": "writer", "status": "done"})

        # ── Stage 4: Editor ─────────────────────────────────────────────
        yield _sse({"stage": "editor", "status": "running"})
        full_draft = "\n\n".join(
            f"## {s['title']}\n{s['content']}" for s in draft_sections
        )
        edited = await self._edit(full_draft)
        yield _sse({"stage": "editor", "status": "done"})

        # ── Stage 5: Presenter ──────────────────────────────────────────
        yield _sse({"stage": "presenter", "status": "running"})
        slide_outline = await self._present(edited)
        yield _sse({"stage": "presenter", "status": "done"})

        # ── Persist & final payload ─────────────────────────────────────
        await self._save(user_id, topic, edited, slide_outline)

        yield _sse({
            "stage": "done",
            "report": edited,
            "slides": slide_outline,
        })

    # ── Stage implementations ─────────────────────────────────────────────

    async def _plan(self, topic: str) -> list[dict]:
        try:
            resp = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=PLANNER_PROMPT,
                user=f"Topic: {topic}",
                max_tokens=1024,
                temperature=0.3,
            )
            return json.loads(resp.text)
        except Exception:
            # Fallback outline
            return [
                {"title": "Introduction", "description": "Overview of the topic."},
                {"title": "Background", "description": "Historical and theoretical context."},
                {"title": "Key Concepts", "description": "Core ideas and definitions."},
                {"title": "Current Developments", "description": "Recent advances."},
                {"title": "Conclusion", "description": "Summary and future directions."},
            ]

    async def _research(self, topic: str, sections: list[dict]) -> str:
        """Gather research notes for all sections concurrently."""
        async def _research_section(section: dict) -> str:
            try:
                resp = await llm.complete(
                    model="claude-haiku-4-5-20251001",
                    system=RESEARCHER_PROMPT,
                    user=f"Topic: {topic}\nSection: {section.get('title')}\n{section.get('description', '')}",
                    max_tokens=512,
                    temperature=0.3,
                )
                return f"### {section.get('title')}\n{resp.text}"
            except Exception:
                return f"### {section.get('title')}\n- Research data unavailable."

        notes = await asyncio.gather(*[_research_section(s) for s in sections])
        return "\n\n".join(notes)

    async def _write(self, sections: list[dict], research_notes: str) -> list[dict]:
        """Write each section concurrently."""
        async def _write_section(section: dict) -> dict:
            try:
                resp = await llm.complete(
                    model="claude-sonnet-4-20250514",
                    system=WRITER_PROMPT,
                    user=f"Section title: {section.get('title')}\nResearch notes:\n{research_notes[:3000]}\n\nWrite this section now.",
                    max_tokens=1024,
                    temperature=0.5,
                )
                return {"title": section.get("title", ""), "content": resp.text}
            except Exception:
                return {"title": section.get("title", ""), "content": "Content generation failed."}

        return list(await asyncio.gather(*[_write_section(s) for s in sections]))

    async def _edit(self, draft: str) -> str:
        try:
            resp = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=EDITOR_PROMPT,
                user=draft[:6000],
                max_tokens=4096,
                temperature=0.3,
            )
            return resp.text
        except Exception:
            return draft

    async def _present(self, report: str) -> str:
        try:
            resp = await llm.complete(
                model="claude-haiku-4-5-20251001",
                system=PRESENTER_PROMPT,
                user=report[:4000],
                max_tokens=1024,
                temperature=0.3,
            )
            return resp.text
        except Exception:
            return "SLIDE 1: Report\n• See full report for details"

    async def _save(
        self, user_id: str, topic: str, report_md: str, slide_outline: str
    ) -> None:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            sb.table("research_reports").insert({
                "user_id": user_id,
                "topic": topic,
                "report_md": report_md,
                "slide_outline": slide_outline,
            }).execute()
        except Exception:
            pass

    async def get_report(self, report_id: str, user_id: str) -> dict | None:
        """Fetch a saved research report from Supabase.

        Returns the full report dict or None if not found / not owned by user.
        """
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            row = (
                sb.table("research_reports")
                .select("*")
                .eq("id", report_id)
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            return row.data[0] if row.data else None
        except Exception:
            return None


# Singleton
auto_researcher = AutoResearcher()
