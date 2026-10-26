from __future__ import annotations
import logging
from typing import Any, List, Optional
from db.repositories.course_repo import CourseRepository
from db.repositories.course_tariff_repo import CourseTariffRepository
from services.cohort_service import format_course_title_with_cohort

logger = logging.getLogger(__name__)

class CourseService:
    def __init__(
        self,
        course_repo: Optional[CourseRepository] = None,
        tariff_repo: Optional[CourseTariffRepository] = None,
    ) -> None:
        self.course_repo = course_repo or CourseRepository()
        self.tariff_repo = tariff_repo or CourseTariffRepository()

    async def get_all_active_courses(self) -> List[dict[str, Any]]:
        courses = await self.course_repo.list_courses()
        return [dict(c) for c in courses]

    async def get_course_with_tariffs(self, course_id: int) -> Optional[dict[str, Any]]:
        course = await self.course_repo.get_course(course_id)
        if not course:
            return None
        d = dict(course)
        d["tariffs"] = await self.tariff_repo.get_by_course_id(course_id)
        return d
