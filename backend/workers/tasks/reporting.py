"""ReportWeaver — Automated Batch Assessment Report Generator.

Celery task that:
1. Loads all final exam submissions
2. Aggregates score distribution, topic performance, and at-risk students
3. Runs GapFinder to detect teaching gaps
4. Calls claude-sonnet to generate a formal Markdown report
5. Renders the Markdown to PDF via reportlab
6. Uploads to R2 and saves to Supabase ``reports`` table
"""

import asyncio
import json
from io import BytesIO
from statistics import mean, median

from workers.celery_app import celery_app


async def _generate_report_async(
    exam_id: str, institution_id: str, faculty_id: str
) -> dict:
    from core.llm import llm
    from core.storage import storage
    from config import get_settings
    from supabase import create_client
    from engines.iae.gap_finder import gap_finder

    settings = get_settings()
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

    # 1. Load final submissions
    rows = (
        sb.table("exam_submissions")
        .select("student_id, score, answers, grading_detail")
        .eq("exam_id", exam_id)
        .eq("grading_status", "final")
        .execute()
    )
    submissions = rows.data or []

    if not submissions:
        return {"status": "error", "message": "No final submissions found."}

    scores = [float(s.get("score") or 0) for s in submissions]
    total = len(scores)
    avg = mean(scores) if scores else 0
    med = median(scores) if scores else 0

    # Score distribution buckets
    distribution = {
        "0-40 (fail)": sum(1 for s in scores if s <= 40),
        "41-60": sum(1 for s in scores if 40 < s <= 60),
        "61-80": sum(1 for s in scores if 60 < s <= 80),
        "81-100": sum(1 for s in scores if s > 80),
    }

    # At-risk students (score <= 40)
    at_risk = [
        s.get("student_id") for s in submissions
        if float(s.get("score") or 0) <= 40
    ]

    # Gap analysis
    gaps_data = await gap_finder.analyze(institution_id)

    REPORT_PROMPT = """\
Generate a professional faculty batch performance report in formal academic Markdown.

Data:
- Total students: {total}
- Average score: {avg:.1f}
- Median score: {med:.1f}
- Score distribution: {distribution}
- At-risk students (≤40%): {at_risk_count}
- Learning gaps identified: {gaps}

Include:
1. Executive Summary (3–4 sentences)
2. Score Distribution Analysis with observations
3. At-Risk Student Summary
4. Learning Gap Analysis (coverage gaps / performance gaps / blind spots)
5. Recommended Interventions for faculty
6. Conclusion

Write in formal academic report style. Use ## for section headings.
"""

    response = await llm.complete(
        model="claude-sonnet-4-20250514",
        system=REPORT_PROMPT.format(
            total=total,
            avg=avg,
            med=med,
            distribution=json.dumps(distribution),
            at_risk_count=len(at_risk),
            gaps=json.dumps(gaps_data.get("gaps", [])[:10]),
        ),
        user="Generate the report.",
        max_tokens=4096,
        temperature=0.3,
    )
    report_md = response.text

    # 2. Render to PDF
    pdf_bytes = _render_pdf(report_md)

    # 3. Upload to R2
    pdf_key = f"reports/{institution_id}/{exam_id}/batch_report.pdf"
    await storage.upload(pdf_key, pdf_bytes, "application/pdf")

    # 4. Save record to Supabase
    sb.table("reports").insert({
        "exam_id": exam_id,
        "institution_id": institution_id,
        "faculty_id": faculty_id,
        "r2_key": pdf_key,
        "report_md": report_md,
        "at_risk_count": len(at_risk),
    }).execute()

    return {
        "status": "done",
        "pdf_key": pdf_key,
        "total_students": total,
        "avg_score": round(avg, 2),
        "at_risk_count": len(at_risk),
    }


def _render_pdf(markdown_text: str) -> bytes:
    """Convert a Markdown report to a clean PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib import colors

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
                story.append(Spacer(1, 0.3 * cm))
                story.append(Paragraph(stripped[3:], styles["Heading2"]))
            elif stripped.startswith("# "):
                story.append(Paragraph(stripped[2:], styles["Heading1"]))
            elif stripped.startswith("- ") or stripped.startswith("* "):
                story.append(Paragraph(f"&bull; {stripped[2:]}", styles["Normal"]))
            elif stripped:
                story.append(Paragraph(stripped, styles["Normal"]))
            else:
                story.append(Spacer(1, 0.25 * cm))

        doc.build(story)
        return buf.getvalue()
    except Exception:
        return b"%PDF-placeholder"


@celery_app.task(name="generate_batch_report", bind=True, max_retries=2)
def generate_batch_report(self, exam_id: str, institution_id: str, faculty_id: str):
    """Celery task: generate and upload a batch performance report for an exam."""
    try:
        result = asyncio.run(
            _generate_report_async(exam_id, institution_id, faculty_id)
        )
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
