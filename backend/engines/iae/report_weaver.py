"""ReportWeaver — Automated Batch Assessment Report Engine.

This module exposes the ReportWeaver class that encapsulates the LLM
report-generation logic. The Celery task in workers/tasks/reporting.py
calls this engine to decouple the orchestration layer from the LLM logic.

Pipeline:
1. Load all finalized (grading_status='final') submissions for the exam
2. Aggregate score statistics and at-risk students
3. Run GapFinder to detect teaching/curriculum gaps
4. Ask claude-sonnet to produce a formal Markdown batch report
5. Render Markdown → PDF (reportlab)
6. Upload PDF to R2 and record in Supabase ``reports`` table

Used by:
  - workers/tasks/reporting.py (Celery async execution)
  - POST /faculty/exams/{exam_id}/report (triggers the Celery task)
"""

import json
from io import BytesIO
from statistics import mean, median


REPORT_PROMPT = """\
Generate a professional faculty batch performance report in formal academic Markdown.

Exam Data:
- Total students: {total}
- Average score: {avg:.1f}
- Median score: {med:.1f}
- Score distribution: {distribution}
- At-risk students (≤40%): {at_risk_count}
- Learning gaps identified: {gaps}

Include ALL of these sections:
1. Executive Summary (3–4 sentences describing overall cohort performance)
2. Score Distribution Analysis (with key observations about spread and outliers)
3. At-Risk Student Summary (count and intervention urgency)
4. Learning Gap Analysis (coverage gaps / performance gaps / blind spots)
5. Recommended Interventions for faculty (concrete, actionable steps)
6. Conclusion

Write in formal academic report style. Use ## for section headings.
Do NOT include any JSON. Write narrative prose.
"""


class ReportWeaver:
    """Generates formal batch assessment reports for faculty."""

    async def generate(self, exam_id: str, institution_id: str, faculty_id: str) -> dict:
        """Generate a batch report for a completed, graded exam.

        Args:
            exam_id: The exam to report on.
            institution_id: Institution slug.
            faculty_id: Faculty member requesting the report.

        Returns:
            {status, pdf_key, report_md, total_students, avg_score, at_risk_count}
        """
        from core.llm import llm
        from core.storage import storage
        from config import get_settings
        from supabase import create_client
        from engines.iae.gap_finder import gap_finder

        settings = get_settings()
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

        # ── 1. Load final submissions ────────────────────────────────────────
        rows = (
            sb.table("exam_submissions")
            .select("student_id, score, grading_detail")
            .eq("exam_id", exam_id)
            .eq("grading_status", "final")
            .execute()
        )
        submissions = rows.data or []

        if not submissions:
            return {
                "status": "error",
                "message": "No finalized submissions found. Approve submissions before generating a report.",
            }

        scores = [float(s.get("score") or 0) for s in submissions]
        total = len(scores)
        avg = mean(scores) if scores else 0.0
        med = median(scores) if scores else 0.0

        distribution = {
            "0-40 (fail)": sum(1 for s in scores if s <= 40),
            "41-60": sum(1 for s in scores if 40 < s <= 60),
            "61-80": sum(1 for s in scores if 60 < s <= 80),
            "81-100": sum(1 for s in scores if s > 80),
        }

        at_risk_count = sum(1 for s in scores if s <= 40)

        # ── 2. Teaching gap analysis ─────────────────────────────────────────
        gaps_data = await gap_finder.analyze(institution_id)

        # ── 3. LLM report generation ─────────────────────────────────────────
        response = await llm.complete(
            model="claude-sonnet-4-20250514",
            system=REPORT_PROMPT.format(
                total=total,
                avg=avg,
                med=med,
                distribution=json.dumps(distribution),
                at_risk_count=at_risk_count,
                gaps=json.dumps(gaps_data.get("gaps", [])[:10], indent=2),
            ),
            user="Generate the report now.",
            max_tokens=4096,
            temperature=0.3,
        )
        report_md = response.text

        # ── 4. Render to PDF ─────────────────────────────────────────────────
        pdf_bytes = self._render_pdf(report_md)

        # ── 5. Upload to R2 ──────────────────────────────────────────────────
        pdf_key = f"reports/{institution_id}/{exam_id}/batch_report.pdf"
        await storage.upload(pdf_key, pdf_bytes, "application/pdf")

        # ── 6. Persist record ────────────────────────────────────────────────
        sb.table("reports").upsert({
            "exam_id": exam_id,
            "institution_id": institution_id,
            "faculty_id": faculty_id,
            "r2_key": pdf_key,
            "report_md": report_md,
        }).execute()

        return {
            "status": "done",
            "pdf_key": pdf_key,
            "report_md": report_md,
            "total_students": total,
            "avg_score": round(avg, 2),
            "at_risk_count": at_risk_count,
        }

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _render_pdf(markdown_text: str) -> bytes:
        """Convert a Markdown report to a clean A4 PDF using reportlab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

            buf = BytesIO()
            doc = SimpleDocTemplate(
                buf, pagesize=A4,
                topMargin=2 * cm, bottomMargin=2 * cm,
                leftMargin=2.5 * cm, rightMargin=2.5 * cm,
            )
            styles = getSampleStyleSheet()
            story = []

            for line in markdown_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("## "):
                    story.append(Spacer(1, 0.4 * cm))
                    story.append(Paragraph(stripped[3:], styles["Heading2"]))
                elif stripped.startswith("# "):
                    story.append(Paragraph(stripped[2:], styles["Heading1"]))
                elif stripped.startswith(("- ", "* ")):
                    story.append(Paragraph(f"&bull; {stripped[2:]}", styles["Normal"]))
                elif stripped:
                    story.append(Paragraph(stripped, styles["Normal"]))
                else:
                    story.append(Spacer(1, 0.25 * cm))

            doc.build(story)
            return buf.getvalue()
        except Exception:
            return b"%PDF-placeholder"


# Singleton
report_weaver = ReportWeaver()
