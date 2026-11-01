from __future__ import annotations

import logging
from fastapi import APIRouter, Depends

from db.database import database
from db.repositories.user_repo import UserRepository
from services.analytics_service import AnalyticsService
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _get_analytics_service() -> AnalyticsService:
    return AnalyticsService.create_default(database.conn)


@router.get("/overview")
@router.get("/admin/overview")
async def get_platform_admin_overview(
    telegram_id: int = Depends(get_current_telegram_id),
    service: AnalyticsService = Depends(_get_analytics_service),
) -> dict:
    """Super admin uchun platformaning to'liq ko'rsatkichlari (foydalanuvchilar, savdo, kurslar)."""
    return await service.get_platform_overview()


@router.get("/courses/{course_id}/my-progress")
async def my_progress(
    course_id: int | str,
    telegram_id: int = Depends(get_current_telegram_id),
    service: AnalyticsService = Depends(_get_analytics_service),
) -> list[dict]:
    clean_course_id = int(str(course_id).replace("course-", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    return await service.get_student_progress(user.id, clean_course_id)


@router.get("/cabinets/activity")
@router.get("/cabinets/{cabinet_id}/activity")
async def get_cabinet_students_activity(
    cabinet_id: str | int | None = None,
    mentor_id: str | int | None = None,
    telegram_id: int = Depends(get_current_telegram_id),
    service: AnalyticsService = Depends(_get_analytics_service),
) -> list[dict]:
    """Super admin / mentor uchun platformadagi o'quvchilar faolligi va darslarni o'zlashtirish statistikasi."""
    return await service.get_cabinet_students_activity(
        cabinet_id=cabinet_id,
        mentor_id=mentor_id,
    )
