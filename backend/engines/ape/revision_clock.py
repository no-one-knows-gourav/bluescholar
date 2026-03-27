"""RevisionClock — Adaptive Revision Planner + Dynamic Daily To-Do.

Responsibilities:
1. Generate a day-by-day revision schedule (LLM-powered, Sonnet).
2. Expose a daily to-do list derived from the master schedule.
3. Let students tick tasks done/skipped — persisted in ``revision_todos``.
4. Rebalance the schedule when a student misses a day.

Supabase tables used:
- ``revision_schedules`` — master schedule (per student)
- ``revision_todos``    — daily task completion status
"""

import json
from datetime import date, datetime, timezone, timedelta


PLANNER_PROMPT = """\
Generate a day-by-day revision schedule as a JSON array.

Input data:
- Syllabus: {syllabus}
- Exam date: {exam_date}
- Today: {today}
- Weak topics (prioritise these): {weak_topics}
- Strong topics (reduce time): {strong_topics}

Rules:
1. Allocate more time to weak topics and high-weightage units.
2. Leave the final 2 days before the exam as "full revision" days (no new topics).
3. Maximum 4 topics per day.
4. Include at least one rest day per week (tasks: []).
5. Each task has a `type`: "study" (new material), "revise" (review), or "practice" (questions).

Return ONLY this JSON — no markdown, no preamble:
[
  {
    "date": "YYYY-MM-DD",
    "tasks": [
      {
        "topic": "...",
        "unit": 1,
        "duration_mins": 60,
        "priority": "high|medium|low",
        "type": "study|revise|practice"
      }
    ]
  }
]

Be concise. Answer in under 150 words unless the question requires more detail.
Use bullet points only when listing 3+ distinct items.
"""


class RevisionClock:
    """LLM-generated revision schedule with a dynamic daily to-do system."""

    # ── Schedule generation ───────────────────────────────────────────────

    async def generate(
        self,
        user_id: str,
        institution_id: str,
        exam_date: date,
    ) -> list[dict]:
        """Build a full revision schedule from today until the exam.

        Args:
            user_id: Student's user ID.
            institution_id: Used to load syllabus.
            exam_date: Target exam date.

        Returns:
            List of day dicts: [{date, tasks}]
        """
        from core.llm import llm
        from engines.ape.study_time_predictor import study_time_predictor

        syllabus = await self._get_syllabus(institution_id)
        weak_topics = await self._get_weak_topics(user_id)
        strong_topics = await self._get_strong_topics(user_id)
        peak_data = await study_time_predictor.predict(user_id)
        peak_windows = peak_data.get("peak_windows") or ["morning", "evening"]

        syllabus_json = json.dumps(syllabus, indent=2) if syllabus else "Not available"

        response = await llm.complete(
            model="claude-haiku-4-5",
            system=PLANNER_PROMPT.format(
                syllabus=syllabus_json[:4000],
                exam_date=str(exam_date),
                today=str(date.today()),
                weak_topics=json.dumps(weak_topics[:10]),
                strong_topics=json.dumps(strong_topics[:10]),
            ),
            user=f"Peak study windows for this student: {', '.join(peak_windows)}. Generate the revision schedule, scheduling difficult topics during these peak windows.",
            max_tokens=4096,
            temperature=0.3,
        )

        # Strip markdown fences if LLM wraps JSON in ```json ... ```
        raw = response.text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) >= 2 else raw
        try:
            schedule = json.loads(raw)
            if not isinstance(schedule, list):
                schedule = []
        except json.JSONDecodeError:
            schedule = []

        # Persist master schedule
        await self._save_schedule(user_id, schedule, exam_date)

        # Seed today's to-do rows
        await self._seed_today_todos(user_id, schedule)

        return schedule

    async def get_schedule(self, user_id: str) -> dict:
        """Fetch the stored revision schedule."""
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            row = (
                sb.table("revision_schedules")
                .select("schedule, exam_date, updated_at")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if row.data:
                return row.data[0]
        except Exception:
            pass
        return {}

    # ── Daily To-Do ───────────────────────────────────────────────────────

    async def get_today_todos(self, user_id: str) -> dict:
        """Return today's to-do list with live completion status.

        Auto-seeds rows for today if not yet created (daily rollover).

        Returns:
            {date, todos: [{task_key, topic, unit, duration_mins, priority, type, status}],
             completion_rate: float}
        """
        today_str = str(date.today())

        # Ensure today's rows exist (handles day rollover)
        schedule_data = await self.get_schedule(user_id)
        schedule = schedule_data.get("schedule", [])
        if schedule:
            await self._seed_today_todos(user_id, schedule)

        todos = await self._load_todos(user_id, today_str)

        done_count = sum(1 for t in todos if t.get("status") == "done")
        total = len(todos)
        rate = round(done_count / total, 2) if total else 0.0

        return {
            "date": today_str,
            "todos": todos,
            "completion_rate": rate,
        }

    async def update_todo_status(
        self,
        user_id: str,
        task_key: str,
        status: str,
    ) -> dict:
        """Mark a to-do item as done / skipped / pending.

        Args:
            user_id: Student's user ID.
            task_key: Unique task identifier (format: YYYY-MM-DD__idx).
            status: One of "pending", "done", "skipped".

        Returns:
            Updated to-do list for today.
        """
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            (
                sb.table("revision_todos")
                .update({
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                .eq("user_id", user_id)
                .eq("task_key", task_key)
                .execute()
            )
        except Exception:
            pass

        return await self.get_today_todos(user_id)

    # ── Rebalance ─────────────────────────────────────────────────────────

    async def rebalance(self, user_id: str, missed_dates: list[str]) -> list[dict]:
        """Redistribute incomplete tasks from missed days across future days.

        Args:
            user_id: Student's user ID.
            missed_dates: List of date strings ("YYYY-MM-DD") the student missed.

        Returns:
            Updated schedule list.
        """
        schedule_data = await self.get_schedule(user_id)
        schedule: list[dict] = list(schedule_data.get("schedule", []))
        if not schedule:
            return []

        today = date.today()

        # Collect tasks from missed days
        missed_tasks: list[dict] = []
        for day in schedule:
            if day.get("date") in missed_dates:
                missed_tasks.extend(day.get("tasks", []))

        # Future days (from tomorrow onwards, excluding the last 2 — revision buffer)
        future_days = [
            d for d in schedule
            if d.get("date") and date.fromisoformat(d["date"]) > today
        ][:-2]  # keep last 2 as pure-revision buffer

        if not future_days or not missed_tasks:
            return schedule

        # Spread missed tasks evenly using round-robin
        for idx, task in enumerate(missed_tasks):
            target_day = future_days[idx % len(future_days)]
            existing = target_day.get("tasks", [])
            if len(existing) < 4:  # max 4 tasks/day
                existing.append(task)
                target_day["tasks"] = existing

        exam_date_str = schedule_data.get("exam_date", "")
        exam_date = date.fromisoformat(exam_date_str) if exam_date_str else today + timedelta(days=30)
        await self._save_schedule(user_id, schedule, exam_date)

        return schedule

    # ── Private helpers ───────────────────────────────────────────────────

    async def _get_syllabus(self, institution_id: str) -> dict | None:
        from engines.ace.syllabus_mapper import syllabus_mapper
        return await syllabus_mapper.get_syllabus(institution_id)

    async def _get_weak_topics(self, user_id: str) -> list[str]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("weak_spots")
                .select("concept")
                .eq("user_id", user_id)
                .order("score", desc=False)
                .limit(10)
                .execute()
            )
            return [r["concept"] for r in (rows.data or [])]
        except Exception:
            return []

    async def _get_strong_topics(self, user_id: str) -> list[str]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("mock_results")
                .select("topic")
                .eq("user_id", user_id)
                .gte("score", 80)
                .execute()
            )
            return list({r["topic"] for r in (rows.data or []) if r.get("topic")})
        except Exception:
            return []

    async def _save_schedule(
        self, user_id: str, schedule: list[dict], exam_date: date
    ) -> None:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            sb.table("revision_schedules").upsert({
                "user_id": user_id,
                "schedule": schedule,
                "exam_date": str(exam_date),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception:
            pass

    async def _seed_today_todos(self, user_id: str, schedule: list[dict]) -> None:
        """Insert today's to-do rows if they don't already exist."""
        today_str = str(date.today())
        today_tasks: list[dict] = []
        for day in schedule:
            if day.get("date") == today_str:
                today_tasks = day.get("tasks", [])
                break

        if not today_tasks:
            return

        # Check if already seeded
        existing = await self._load_todos(user_id, today_str)
        if existing:
            return

        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = []
            for idx, task in enumerate(today_tasks):
                task_key = f"{today_str}__{idx}"
                rows.append({
                    "user_id": user_id,
                    "task_key": task_key,
                    "date": today_str,
                    "topic": task.get("topic", ""),
                    "unit": task.get("unit"),
                    "duration_mins": task.get("duration_mins", 60),
                    "priority": task.get("priority", "medium"),
                    "type": task.get("type", "study"),
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
            if rows:
                sb.table("revision_todos").insert(rows).execute()
        except Exception:
            pass

    async def _load_todos(self, user_id: str, date_str: str) -> list[dict]:
        try:
            from config import get_settings
            from supabase import create_client
            settings = get_settings()
            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            rows = (
                sb.table("revision_todos")
                .select("*")
                .eq("user_id", user_id)
                .eq("date", date_str)
                .order("task_key")
                .execute()
            )
            return rows.data or []
        except Exception:
            return []


# Singleton
revision_clock = RevisionClock()
