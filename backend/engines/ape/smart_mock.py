"""SmartMock — Personalized Mock Paper Generator.

Builds an exam paper by:
1. Reading syllabus unit weightage
2. Pulling the student's question bank (built by QuestionForge)
3. Overweighting weak topics (2× sampling probability)
4. Selecting questions to fit each unit's mark budget
5. Rendering a PDF via reportlab
"""

import random
from io import BytesIO
from core.vector import qdrant
from core.embeddings import embeddings


class SmartMock:
    """Generates a personalized mock exam paper from the student's question bank."""

    async def generate(self, user_id: str, institution_id: str) -> dict:
        """Build a weighted mock paper and render it to a PDF buffer.

        Args:
            user_id: The student's user ID.
            institution_id: Institution slug for Qdrant / Supabase namespacing.

        Returns:
            Dict with ``mock_id``, ``pdf_url`` (R2 signed URL), and ``questions`` list.
        """
        # 1. Fetch syllabus structure from Qdrant
        syllabus = await self._get_syllabus(institution_id)
        if not syllabus:
            return {
                "error": "No syllabus found. Upload a syllabus first.",
                "mock_id": None,
                "pdf_url": None,
                "questions": [],
            }

        # 2. Fetch weak spots — stub (empty until WeakSpotter is built)
        weak_topics: dict[str, float] = await self._get_weak_topics(user_id)

        # 3. Fetch questions from Qdrant question bank index
        all_questions = await self._get_question_bank(user_id, institution_id)
        if not all_questions:
            return {
                "error": "No questions in bank. Forge questions from your documents first.",
                "mock_id": None,
                "pdf_url": None,
                "questions": [],
            }

        # 4. Select questions respecting unit budgets, overweighting weak topics
        selected = self._select_questions(syllabus, all_questions, weak_topics)

        if not selected:
            return {
                "error": "Could not assemble a mock paper from the available questions.",
                "mock_id": None,
                "pdf_url": None,
                "questions": [],
            }

        # 5. Render PDF
        pdf_bytes = self._render_pdf(selected, user_id)

        # 6. Upload to R2 and save mock record (best-effort)
        mock_id, pdf_url = await self._save_mock(
            pdf_bytes, selected, user_id, institution_id
        )

        return {
            "mock_id": mock_id,
            "pdf_url": pdf_url,
            "questions": selected,
        }

    # ── Selection logic ───────────────────────────────────────────────────

    def _select_questions(
        self,
        syllabus: dict,
        questions: list[dict],
        weak_topics: dict[str, float],
    ) -> list[dict]:
        """Select questions fitting unit mark budgets, overweighting weak topics."""
        selected: list[dict] = []

        for unit in syllabus.get("units", []):
            unit_number = unit.get("unit_number")
            unit_budget = unit.get("weightage_marks", 20)

            # Questions matching this unit
            unit_qs = [
                q for q in questions
                if q.get("unit") == unit_number or q.get("unit") == str(unit_number)
            ]
            if not unit_qs:
                # Fallback: use any questions if unit matching is unavailable
                unit_qs = questions

            # Build weighted pool: 2× for weak topics, 1× otherwise
            weighted_pool: list[dict] = []
            for q in unit_qs:
                weight = 2 if q.get("topic") in weak_topics else 1
                weighted_pool.extend([q] * weight)

            random.shuffle(weighted_pool)

            allocated = 0
            seen_ids: set = set()
            for q in weighted_pool:
                q_id = q.get("id") or id(q)
                marks = q.get("marks", 2)
                if q_id not in seen_ids and allocated + marks <= unit_budget:
                    selected.append(q)
                    seen_ids.add(q_id)
                    allocated += marks

        return selected

    # ── PDF rendering ─────────────────────────────────────────────────────

    def _render_pdf(self, questions: list[dict], user_id: str) -> bytes:
        """Render questions to a clean exam PDF using reportlab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
            )

            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4,
                                    topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=2.5*cm, rightMargin=2.5*cm)

            styles = getSampleStyleSheet()
            bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold")
            normal = styles["Normal"]
            heading = styles["Heading1"]

            story = []

            # Header
            story.append(Paragraph("BlueScholar — Mock Examination", heading))
            story.append(Paragraph(f"Total Marks: {sum(q.get('marks', 2) for q in questions)}", bold))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
            story.append(Spacer(1, 0.4*cm))

            # Questions
            for i, q in enumerate(questions, start=1):
                qtext = f"Q{i}. {q.get('question', '')}"
                marks_label = f"[{q.get('marks', 2)} marks]"
                story.append(Paragraph(f"<b>{qtext}</b>  <i>{marks_label}</i>", normal))

                # MCQ options
                if q.get("question_type") == "MCQ" and q.get("options"):
                    for opt in q["options"]:
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{opt}", normal))

                story.append(Spacer(1, 0.6*cm))

            doc.build(story)
            return buf.getvalue()

        except Exception:
            # If reportlab is missing/fails, return a minimal placeholder bytes
            return b"%PDF-placeholder"

    # ── Data fetchers (with graceful stubs) ───────────────────────────────

    async def _get_syllabus(self, institution_id: str) -> dict | None:
        """Reconstruct syllabus structure from Qdrant."""
        from engines.ace.syllabus_mapper import syllabus_mapper
        return await syllabus_mapper.get_syllabus(institution_id)

    async def _get_weak_topics(self, user_id: str) -> dict[str, float]:
        """Fetch student's weak spots from Supabase. Stub returns empty dict."""
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
                .limit(10)
                .execute()
            )
            return {r["concept"]: r["score"] for r in (rows.data or [])}
        except Exception:
            return {}

    async def _get_question_bank(self, user_id: str, institution_id: str) -> list[dict]:
        """Fetch questions from Supabase question_bank.
        Falls back to empty list if the table doesn't exist yet.
        """
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("question_bank")
                .select("*")
                .eq("user_id", user_id)
                .eq("institution_id", institution_id)
                .execute()
            )
            return rows.data or []
        except Exception:
            return []

    async def _save_mock(
        self,
        pdf_bytes: bytes,
        questions: list[dict],
        user_id: str,
        institution_id: str,
    ) -> tuple[str, str]:
        """Upload PDF to R2 and insert mock record in Supabase.
        Returns (mock_id, pdf_url). Degrades gracefully on failure.
        """
        import uuid as _uuid
        mock_id = str(_uuid.uuid4())
        pdf_url = ""

        try:
            from core.storage import storage
            from config import get_settings
            from supabase import create_client

            key = f"mocks/{institution_id}/{user_id}/{mock_id}.pdf"
            await storage.upload(key, pdf_bytes, "application/pdf")
            pdf_url = await storage.get_signed_url(key)

            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            sb.table("mocks").insert({
                "id": mock_id,
                "user_id": user_id,
                "institution_id": institution_id,
                "question_ids": [q.get("id") for q in questions if q.get("id")],
                "pdf_key": key,
                "status": "pending",
            }).execute()
        except Exception:
            pass

        return mock_id, pdf_url


# Singleton
smart_mock = SmartMock()
