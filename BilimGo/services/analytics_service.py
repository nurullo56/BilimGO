from __future__ import annotations

import json
import logging
from typing import Any
from db.repositories.admin_repo import AdminRepository
from db.repositories.lesson_view_repo import LessonViewRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(
        self,
        lesson_view_repo: LessonViewRepository,
        admin_repo: AdminRepository | None = None,
    ) -> None:
        self._lesson_view_repo = lesson_view_repo
        self._admin_repo = admin_repo or AdminRepository(lesson_view_repo._conn)

    @classmethod
    def create_default(cls, conn=None) -> "AnalyticsService":
        """Yagona markazlashgan AnalyticsService fabrikasi."""
        from db.database import database

        c = conn or database.conn
        return cls(
            lesson_view_repo=LessonViewRepository(c),
            admin_repo=AdminRepository(c),
        )

    async def record_view_start(
        self, user_id: int, lesson_id: int, delivery_token_id: int | None = None
    ) -> int:
        return await self._lesson_view_repo.start_view(user_id, lesson_id, delivery_token_id)

    async def record_progress(
        self, view_id: int, watch_duration_sec: int, completion_percent: int
    ) -> None:
        completion_percent = max(0, min(100, completion_percent))
        await self._lesson_view_repo.update_progress(
            view_id, watch_duration_sec, completion_percent
        )

    async def get_student_progress(self, user_id: int, course_id: int) -> list[dict]:
        return await self._lesson_view_repo.student_progress_for_course(user_id, course_id)

    async def get_cabinet_activity(self, cabinet_id: int) -> list[dict]:
        return await self._lesson_view_repo.mentor_students_activity(cabinet_id)

    async def get_platform_overview(self) -> dict[str, Any]:
        """Super admin uchun platformaning to'liq ko'rsatkichlarini qaytaradi."""
        return await self._admin_repo.get_platform_overview()

    async def get_cabinet_students_activity(
        self,
        cabinet_id: str | int | None = None,
        mentor_id: str | int | None = None,
    ) -> list[dict]:
        """Super admin / mentor uchun platformadagi o'quvchilar faolligi va darslarni o'zlashtirish statistikasi."""
        clean_cab_id = None
        if cabinet_id and str(cabinet_id) != "all" and str(cabinet_id) != "":
            try:
                clean_cab_id = int(str(cabinet_id).replace("cab-", ""))
            except ValueError:
                clean_cab_id = None

        clean_mentor_id = None
        if mentor_id and str(mentor_id) != "all" and str(mentor_id) != "":
            try:
                clean_mentor_id = int(str(mentor_id).replace("mentor-", ""))
            except ValueError:
                clean_mentor_id = None

        rows = await self._admin_repo.get_cabinet_students_activity_rows(
            cabinet_id_clean=clean_cab_id,
            mentor_id_clean=clean_mentor_id,
        )

        results = []
        for r in rows:
            branding = {}
            if r.get("branding_config"):
                try:
                    branding = json.loads(r["branding_config"])
                except Exception:
                    branding = {}

            mentor_name = r["mentor_full_name"] or branding.get("mentor_name") or "Bosh Mentor"
            course_title = r["course_title"] or branding.get("course_title") or r["cabinet_name"] or "Kurs"
            mentor_id_val = f"mentor-{r['mentor_user_id']}" if r["mentor_user_id"] else "mentor-1"

            watched = r["lessons_watched"] or 0
            progress_pct = min(100, max(round(r["avg_completion"]), watched * 20))

            status_val = "active"
            if progress_pct >= 90 or watched >= 5:
                status_val = "graduated"
            elif watched == 0:
                status_val = "inactive"

            last_act = "Bugun faol"
            if r["last_activity_time"]:
                last_act = r["last_activity_time"][:16]
            elif r["joined_at"]:
                last_act = r["joined_at"][:10]

            results.append(
                {
                    "user_id": f"st-{r['user_id']}",
                    "full_name": r["full_name"] or f"Talaba #{r['user_id']}",
                    "telegram_id": r["telegram_id"],
                    "username": f"@id{r['telegram_id']}",
                    "lessons_watched": watched,
                    "last_activity": last_act,
                    "progress_percent": progress_pct,
                    "cabinet_id": f"cab-{r['cabinet_id']}",
                    "cabinet_name": r["cabinet_name"],
                    "mentor_id": mentor_id_val,
                    "mentor_name": mentor_name,
                    "course_title": course_title,
                    "status": status_val,
                }
            )

        return results
