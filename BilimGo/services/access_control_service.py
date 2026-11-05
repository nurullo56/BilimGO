from __future__ import annotations

from core.config import settings
from core.exceptions import AccessDeniedError, NotFoundError
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.lesson_repo import Lesson, LessonRepository
from db.repositories.user_repo import UserRepository
from services.adaptive_unlock_service import AdaptiveUnlockService


class AccessControlService:
    def __init__(
        self,
        lesson_repo: LessonRepository,
        access_grant_repo: AccessGrantRepository,
        adaptive_unlock_service: AdaptiveUnlockService | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self._lesson_repo = lesson_repo
        self._access_grant_repo = access_grant_repo
        self._adaptive_unlock_service = adaptive_unlock_service
        self._user_repo = user_repo

    async def ensure_can_watch(self, user_id: int, lesson_id: int) -> Lesson:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise NotFoundError(f"Dars topilmadi: id={lesson_id}")

        if lesson.is_free_preview:
            return lesson

        # Admin, Super Mentor & Mentor barcha darslarni to'siqsiz ko'ra oladi
        if self._user_repo is not None:
            user = await self._user_repo.get_by_id(user_id)
            if user is not None:
                if user.role in ("admin", "super_mentor", "mentor") or user.telegram_id in settings.bot.admin_ids:
                    return lesson

        has_access = await self._access_grant_repo.has_active_access(
            user_id=user_id, lesson_id=lesson_id, course_id=lesson.course_id
        )
        if not has_access:
            raise AccessDeniedError(
                f"Foydalanuvchi {user_id} uchun {lesson_id}-darsga ruxsat yo'q"
            )

        if self._adaptive_unlock_service is not None:
            limit = await self._adaptive_unlock_service.get_effective_limit(
                student_id=user_id, course_id=lesson.course_id
            )
            if limit is not None and lesson.order_index > limit:
                raise AccessDeniedError(
                    f"Ushbu dars hozircha yopiq. Bugungi limitingiz: {limit}-darsgacha (dars tartibi: {lesson.order_index})."
                )

        return lesson

    @classmethod
    def create_default(cls, conn=None) -> AccessControlService:
        from db.database import database
        from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
        from db.repositories.daily_unlock_plan_repo import DailyUnlockPlanRepository
        from db.repositories.unlock_tier_repo import UnlockTierRuleRepository
        connection = conn or database.conn
        adaptive_service = AdaptiveUnlockService(
            plan_repo=DailyUnlockPlanRepository(connection),
            tier_repo=UnlockTierRuleRepository(connection),
            comprehension_repo=ComprehensionCheckRepository(connection),
        )
        return cls(
            lesson_repo=LessonRepository(connection),
            access_grant_repo=AccessGrantRepository(connection),
            adaptive_unlock_service=adaptive_service,
            user_repo=UserRepository(connection),
        )
