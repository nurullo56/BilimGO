from __future__ import annotations

import logging
from typing import Any, List, Optional

from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.course_repo import Course, CourseRepository
from db.repositories.course_tariff_repo import CourseTariffRepository
from db.repositories.user_repo import UserRepository
from db.repositories.waitlist_repo import WaitlistRepository
from services.cohort_service import calculate_course_cohort, format_course_title_with_cohort

logger = logging.getLogger(__name__)


class CourseService:
    """Kurslar, patoklar (cohort) va tariflarni boshqarish servisi."""

    def __init__(
        self,
        course_repo: Optional[CourseRepository] = None,
        tariff_repo: Optional[CourseTariffRepository] = None,
        access_grant_repo: Optional[AccessGrantRepository] = None,
    ) -> None:
        self.course_repo = course_repo or CourseRepository(database.conn)
        self.tariff_repo = tariff_repo or CourseTariffRepository()
        self.access_grant_repo = access_grant_repo or AccessGrantRepository(database.conn)

    async def list_published(self) -> List[Course]:
        """Barcha e'lon qilingan kurslarni qaytaradi."""
        return await self.course_repo.list_published()

    async def get_by_id(self, course_id: int) -> Optional[Course]:
        """Kursni ID bo'yicha oladi."""
        return await self.course_repo.get_by_id(course_id)

    async def get_course_cohort(self, course: Course, user_id: Optional[int] = None) -> str:
        """Kursning joriy patok (cohort) raqamini hisoblaydi."""
        students_count = await self.access_grant_repo.count_cohort_students(course.id)

        enrollment_time = None
        if user_id:
            enrollment_time = await self.access_grant_repo.get_user_course_enrollment_time(user_id, course.id)

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
            "image_url": course.image_url,
            "notice_text": course.notice_text,
            "syllabus": course.syllabus,
            "instructor": course.instructor,
        }
        d["tariffs"] = await self.tariff_repo.get_by_course_id(course_id)
        return d

    async def get_student_courses_progress(self, user_id: int) -> dict[str, Any]:
        """
        Talabaning barcha faol kurslari bo'yicha darslarni yakunlash progressini hisoblaydi.
        Barcha hisob-kitoblar va formatlash servis qatlamida amalga oshiriladi.
        """
        rows = await self.access_grant_repo.get_student_courses_with_progress(user_id)
        if not rows:
            return {"courses": [], "summary_text": ""}

        formatted_rows = []
        text_lines = ["<b>🎓 Sizning faol kurslaringiz:</b>\n"]

        for row in rows:
            total = row["total_lessons"] or 0
            completed = row["completed_lessons"] or 0
            percent = int((completed / total * 100)) if total > 0 else 0

            course = Course.from_row(row)
            formatted_title = await self.get_formatted_title(course, user_id=user_id)

            text_lines.append(f"• <b>{formatted_title}</b>: {completed}/{total} dars ({percent}%)")

            formatted_rows.append({
                "id": row["id"],
                "title": formatted_title,
                "total_lessons": total,
                "completed_lessons": completed,
                "percent": percent,
            })

        return {
            "courses": formatted_rows,
            "summary_text": "\n".join(text_lines),
        }

    async def get_waitlist_status(self, course_id: int, telegram_id: int) -> dict[str, Any]:
        """Kurs kutish ro'yxatidagi foydalanuvchi holati va umumiy navbat soni."""
        user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
        repo = WaitlistRepository(database.conn)
        is_in = await repo.is_in_waitlist(course_id, user.id)
        count = await repo.get_count(course_id)
        return {
            "user": user,
            "is_in_waitlist": is_in,
            "waitlist_count": count,
        }

    async def join_waitlist(self, course_id: int, telegram_id: int) -> dict[str, Any]:
        """Foydalanuvchini kutish ro'yxatiga qo'shish."""
        user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
        repo = WaitlistRepository(database.conn)
        await repo.join_waitlist(course_id, user.id, user.phone)
        count = await repo.get_count(course_id)
        course = await self.course_repo.get_by_id(course_id)
        return {
            "user": user,
            "waitlist_count": count,
            "course_title": course.title if course else "AI Kursi",
        }

    async def leave_waitlist(self, course_id: int, telegram_id: int) -> dict[str, Any]:
        """Foydalanuvchini kutish ro'yxatidan chiqarish."""
        user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
        repo = WaitlistRepository(database.conn)
        await repo.leave_waitlist(course_id, user.id)
        count = await repo.get_count(course_id)
        course = await self.course_repo.get_by_id(course_id)
        return {
            "user": user,
            "waitlist_count": count,
            "course_title": course.title if course else "AI Kursi",
        }

    async def toggle_waitlist(self, course_id: int) -> dict[str, Any]:
        """Kursning waitlist holatini almashtiradi (toggle) va yangi holatni qaytaradi."""
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise ValueError(f"Kurs topilmadi: {course_id}")
        new_status = not course.is_waitlist
        await self.course_repo.update_waitlist_status(course_id, new_status)
        return {
            "course_id": course_id,
            "title": course.title,
            "is_waitlist": new_status,
        }

    async def set_course_notice(self, course_id: int, notice_text: Optional[str]) -> dict[str, Any]:
        """Kursning maxsus e'lon/chegirma matnini yangilaydi."""
        await self.course_repo.update_notice_text(course_id, notice_text)
        course = await self.course_repo.get_by_id(course_id)
        return {
            "course_id": course_id,
            "title": course.title if course else "",
            "notice_text": notice_text,
        }

    async def set_course_image(self, course_id: int, image_url: Optional[str]) -> dict[str, Any]:
        """Kursning muqova rasmini (URL) yangilaydi."""
        await self.course_repo.update_image_url(course_id, image_url)
        course = await self.course_repo.get_by_id(course_id)
        return {
            "course_id": course_id,
            "title": course.title if course else "",
            "image_url": image_url,
        }

    async def set_course_description(self, course_id: int, description: Optional[str]) -> dict[str, Any]:
        """Kursning qisqacha tavsif (description) matnini yangilaydi."""
        await self.course_repo.update_description(course_id, description)
        course = await self.course_repo.get_by_id(course_id)
        return {
            "course_id": course_id,
            "title": course.title if course else "",
            "description": description,
        }
