from __future__ import annotations

from db.repositories.lesson_view_repo import LessonViewRepository


class AnalyticsService:
    def __init__(self, lesson_view_repo: LessonViewRepository) -> None:
        self._lesson_view_repo = lesson_view_repo

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
