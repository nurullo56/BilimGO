from __future__ import annotations

import logging
from typing import Any, List, Optional

from db.database import database
from db.repositories.course_repo import Course, CourseRepository
from db.repositories.course_tariff_repo import CourseTariffRepository
from services.cohort_service import calculate_course_cohort, format_course_title_with_cohort

logger = logging.getLogger(__name__)


class CourseService:
    """Kurslar, patoklar (cohort) va tariflarni boshqarish servisi."""

    def __init__(
        self,
        course_repo: Optional[CourseRepository] = None,
        tariff_repo: Optional[CourseTariffRepository] = None,
    ) -> None:
        self.course_repo = course_repo or CourseRepository(database.conn)
        self.tariff_repo = tariff_repo or CourseTariffRepository()

    async def list_published(self) -> List[Course]:
        """Barcha e'lon qilingan kurslarni qaytaradi."""
        return await self.course_repo.list_published()

    async def get_by_id(self, course_id: int) -> Optional[Course]:
        """Kursni ID bo'yicha oladi."""
        return await self.course_repo.get_by_id(course_id)

    async def get_course_cohort(self, course: Course, user_id: Optional[int] = None) -> str:
        """Kursning joriy patok (cohort) raqamini hisoblaydi."""
        cursor = await database.conn.execute(
            """
            SELECT COUNT(*) as cnt FROM access_grants 
            WHERE course_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            """,
            (course.id,),
        )
        row = await cursor.fetchone()
        students_count = row["cnt"] if row else 1

        enrollment_time = None
        if user_id:
            cursor = await database.conn.execute(
                "SELECT created_at FROM access_grants WHERE user_id = ? AND course_id = ? LIMIT 1",
                (user_id, course.id),
            )
            grant_row = await cursor.fetchone()
            if grant_row:
                enrollment_time = grant_row["created_at"]

        return calculate_course_cohort(
            course_created_at=course.created_at,
            enrollment_time=enrollment_time,
            students_in_month_count=students_count,
        )

    async def get_formatted_title(self, course: Course, user_id: Optional[int] = None) -> str:
        """Kurs nomiga patok raqamini qo'shib qaytaradi (masalan: 'ChinaSeller PRO 1.0')."""
        if course.is_waitlist:
            return course.title
        cohort = await self.get_course_cohort(course, user_id=user_id)
        return format_course_title_with_cohort(course.title, cohort)

    async def get_course_with_tariffs(self, course_id: int, user_id: Optional[int] = None) -> Optional[dict[str, Any]]:
        """Kurs, uning patok raqami va barcha faol tariflarini qaytaradi."""
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            return None
        cohort = await self.get_course_cohort(course, user_id=user_id) if not course.is_waitlist else ""
        formatted_title = course.title if course.is_waitlist else format_course_title_with_cohort(course.title, cohort)
        d = {
            "id": course.id,
            "title": formatted_title,
            "raw_title": course.title,
            "cohort": cohort,
            "is_waitlist": course.is_waitlist,
            "owner_node_id": course.owner_node_id,
            "base_price": course.base_price,
            "status": course.status,
            "description": course.description,
            "created_at": course.created_at,
        }
        d["tariffs"] = await self.tariff_repo.get_by_course_id(course_id)
        return d
