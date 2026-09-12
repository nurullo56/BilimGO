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

        # Admin & Super Mentor barcha darslarni to'siqsiz ko'ra oladi
        if self._user_repo is not None:
            user = await self._user_repo.get_by_id(user_id)
            if user is not None:
                if user.role in ("admin", "super_mentor") or user.telegram_id in settings.bot.admin_ids:
                    return lesson

        has_access = await self._access_grant_repo.has_active_access(
            user_id=user_id, lesson_id=lesson_id, course_id=lesson.course_id
        )
        if has_access:
            return lesson

        raise AccessDeniedError(
            f"Foydalanuvchi {user_id} uchun {lesson_id}-darsga ruxsat yo'q"
        )
