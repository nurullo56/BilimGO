from __future__ import annotations

import logging
from typing import Any, Optional

from db.database import database
from db.repositories.admin_repo import AdminRepository
from db.repositories.course_repo import Course, CourseRepository
from db.repositories.license_node_repo import LicenseNode, LicenseNodeRepository
from db.repositories.tariff_quota_repo import TariffQuota, TariffQuotaRepository
from db.repositories.user_repo import User, UserRepository

logger = logging.getLogger(__name__)


class QuotaService:
    """Mentorlar kvotalari va bepul dostup limitlarini boshqarish servisi."""

    def __init__(
        self,
        admin_repo: Optional[AdminRepository] = None,
        node_repo: Optional[LicenseNodeRepository] = None,
        user_repo: Optional[UserRepository] = None,
        course_repo: Optional[CourseRepository] = None,
        quota_repo: Optional[TariffQuotaRepository] = None,
    ) -> None:
        conn = database.conn
        self.conn = conn
        self.admin_repo = admin_repo or AdminRepository()
        self.node_repo = node_repo or LicenseNodeRepository(conn)
        self.user_repo = user_repo or UserRepository(conn)
        self.course_repo = course_repo or CourseRepository(conn)
        self.quota_repo = quota_repo or TariffQuotaRepository(conn)

    async def get_submentors_list(self) -> list[dict[str, Any]]:
        """Barcha quyi mentorlar ro'yxatini qaytaradi."""
        return await self.admin_repo.get_all_submentors_overview()

    async def get_mentor_quota_overview(self, node_id: int) -> Optional[dict[str, Any]]:
        """
        Mentorning joriy limit holati, litsenziyasi va kurslar bo'yicha limitlar xaritasini oladi.
        """
        node = await self.node_repo.get_by_id(node_id)
        if not node:
            return None

        mentor = await self.user_repo.get_by_id(node.owner_user_id)
        courses = await self.course_repo.list_published()
        quotas_list = await self.quota_repo.list_by_node(node.id)
        quotas_map = {q.course_title: q for q in quotas_list}

        return {
            "node": node,
            "mentor": mentor,
            "courses": courses,
            "quotas_list": quotas_list,
            "quotas_map": quotas_map,
        }

    async def get_course_quota_prompt_data(
        self, node_id: int, course_id: int
    ) -> Optional[dict[str, Any]]:
        """Kurs tanlanganda mentor va kurs bo'yicha ma'lumotlarni oladi."""
        course = await self.course_repo.get_by_id(course_id)
        node = await self.node_repo.get_by_id(node_id)
        mentor = await self.user_repo.get_by_id(node.owner_user_id) if node else None

        if not course or not node or not mentor:
            return None

        quota = await self.quota_repo.get_quota_for_course(node.id, course.title)
        return {
            "node": node,
            "mentor": mentor,
            "course": course,
            "quota": quota,
        }

    async def add_quota_to_mentor(
        self,
        node_id: int,
        course_id: int,
        amount: int,
        tariff_name: str = "standart",
    ) -> Optional[dict[str, Any]]:
        """
        Mentorga muayyan kurs bo'yicha bepul dostup limitini qo'shadi.
        Tranzaksiya ichida amalga oshiriladi.
        """
        course = await self.course_repo.get_by_id(course_id)
        node = await self.node_repo.get_by_id(node_id)
        mentor = await self.user_repo.get_by_id(node.owner_user_id) if node else None

        if not course or not node or not mentor:
            return None

        async with database.transaction():
            updated_quota = await self.quota_repo.add_quota_amount(
                node_id=node.id,
                course_title=course.title,
                add_amount=amount,
                tariff_name=tariff_name,
                course_id=course.id,
            )

        return {
            "node": node,
            "mentor": mentor,
            "course": course,
            "updated_quota": updated_quota,
        }
