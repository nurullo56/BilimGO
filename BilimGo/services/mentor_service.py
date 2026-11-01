from __future__ import annotations

import logging
from typing import Any, Optional

from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.admin_repo import AdminRepository
from db.repositories.course_repo import Course, CourseRepository
from db.repositories.license_node_repo import LicenseNode, LicenseNodeRepository
from db.repositories.mentor_application_repo import MentorApplication, MentorApplicationRepository
from db.repositories.tariff_quota_repo import TariffQuotaRepository
from db.repositories.user_repo import User, UserRepository
from services.cabinet_service import CabinetService

logger = logging.getLogger(__name__)


class MentorService:
    """Mentorlarni tayinlash, boshqarish va axborotini olish servisi."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        license_node_repo: Optional[LicenseNodeRepository] = None,
        quota_repo: Optional[TariffQuotaRepository] = None,
        cabinet_service: Optional[CabinetService] = None,
        course_repo: Optional[CourseRepository] = None,
        access_grant_repo: Optional[AccessGrantRepository] = None,
        admin_repo: Optional[AdminRepository] = None,
        app_repo: Optional[MentorApplicationRepository] = None,
    ) -> None:
        conn = database.conn
        self.conn = conn
        self.user_repo = user_repo or UserRepository(conn)
        self.license_node_repo = license_node_repo or LicenseNodeRepository(conn)
        self.quota_repo = quota_repo or TariffQuotaRepository(conn)
        self.cabinet_service = cabinet_service or CabinetService.create_default(conn)
        self.course_repo = course_repo or CourseRepository(conn)
        self.access_grant_repo = access_grant_repo or AccessGrantRepository(conn)
        self.admin_repo = admin_repo or AdminRepository()
        self.app_repo = app_repo or MentorApplicationRepository(conn)

    async def get_target_user_and_courses(
        self, target_tid: int
    ) -> tuple[User, str, list[Course]]:
        """Mentor qilinayotgan foydalanuvchi va mavjud kurslar ro'yxatini oladi."""
        target_user = await self.user_repo.get_or_create(telegram_id=target_tid)
        display_name = target_user.full_name or f"Foydalanuvchi #{target_tid}"
        courses = await self.course_repo.list_published()
        return target_user, display_name, courses

    async def assign_mentor(
        self,
        target_tid: int,
        course_id: int = 1,
        tariff_name: str = "standart",
    ) -> dict[str, Any]:
        """
        Nomzodni mentor sifatida to'liq tayinlaydi:
        1. User rolini 'mentor' ga yangilaydi
        2. Litsenziya tugunini (license_nodes) topadi yoki yaratadi
        3. Tarif bo'yicha 15 kunlik bepul sinov kvotalarini shakllantiradi
        4. O'quv kabinetini yaratadi
        5. Barcha nashr qilingan kurslarga to'liq kirish huquqini ochadi
        Barcha DB operatsiyalari xavfsiz transaction ichida bajariladi.
        """
        async with database.transaction():
            target_user = await self.user_repo.get_or_create(telegram_id=target_tid)
            await self.user_repo.update_role(target_user.id, "mentor")

            node = await self.license_node_repo.get_by_owner_id(target_user.id)
            if not node:
                node_id = await self.license_node_repo.create_node(
                    owner_user_id=target_user.id,
                    course_id=course_id,
                    parent_id=1,
                    royalty_percent=20.0,
                    stage="limit",
                    status="active",
                )
            else:
                node_id = node.id
                await self.license_node_repo.update_course_id(node_id, course_id)

            # 15 kunlik bepul limit kvotalarini shakllantirish
            await self.quota_repo.initialize_quotas_for_tariff(node_id, tariff_name)

            # O'quv kabinetini shakllantirish
            cabinet = await self.cabinet_service.get_or_create_for_node(node_id)

            # Barcha kurslarga mentor uchun dostup ochish
            all_courses = await self.course_repo.list_published()
            for c in all_courses:
                try:
                    await self.access_grant_repo.grant_course_access(
                        target_user.id, c.id, granted_via_sale_id=0
                    )
                except Exception as e:
                    logger.warning(
                        "Mentor %s ga kurs %s ruxsatini berishda ogohlantirish: %s",
                        target_user.id,
                        c.id,
                        e,
                    )

            selected_course = await self.course_repo.get_by_id(course_id)
            course_title = (
                selected_course.title if selected_course else f"Kurs #{course_id}"
            )

        return {
            "target_user": target_user,
            "node_id": node_id,
            "cabinet": cabinet,
            "all_courses": all_courses,
            "course_title": course_title,
        }

    async def list_all_submentors_overview(self) -> list[dict[str, Any]]:
        """Barcha quyi mentorlar haqidagi umumiy ma'lumotlarni qaytaradi."""
        return await self.admin_repo.get_all_submentors_overview()

    async def get_mentor_node(self, mentor_user_id: int) -> Optional[LicenseNode]:
        """Mentorning eng so'nggi litsenziya tugunini oladi."""
        return await self.license_node_repo.get_by_owner_id(mentor_user_id)

    async def get_mentor_statistics(self, mentor_user_id: int) -> Optional[dict[str, Any]]:
        """
        Mentor kabinetining barcha statistika ma'lumotlarini to'playdi:
        - Litsenziya tuguni va bosqichi (stage)
        - Limit davri kvotalari
        - Shogirdlar AI tyutor xarajatlari
        - Shogirdlar Server va video stream xarajatlari
        - Talabalar dars ko'rish faolligi
        """
        from db.repositories.ai_token_repo import AITokenRepository
        from db.repositories.lesson_view_repo import LessonViewRepository
        from db.repositories.server_expense_repo import ServerExpenseRepository

        node = await self.get_mentor_node(mentor_user_id)
        if not node:
            return None

        # Limit kvotalari
        quotas = []
        if node.stage == "limit":
            quotas = await self.quota_repo.list_by_node(node.id)

        # AI va Server xarajatlari
        ai_repo = AITokenRepository(self.conn)
        server_repo = ServerExpenseRepository(self.conn)
        ai_summary = await ai_repo.get_mentor_summary(mentor_user_id)
        server_summary = await server_repo.get_mentor_summary(mentor_user_id)

        # Talabalar faolligi
        lv_repo = LessonViewRepository(self.conn)
        cabinet_ids = await self.cabinet_service._cabinet_repo.get_owned_cabinet_ids(mentor_user_id)
        students_activity: list[dict] = []
        for cid in cabinet_ids:
            activity = await lv_repo.mentor_students_activity(cid)
            students_activity.extend(activity)

        return {
            "node": node,
            "stage": node.stage,
            "stage_started": node.stage_started_at,
            "quotas": quotas,
            "ai_summary": ai_summary,
            "server_summary": server_summary,
            "students_activity": students_activity,
        }

    async def get_mentor_referral_data(
        self, mentor_user_id: int
    ) -> Optional[tuple[int, list[Course]]]:
        """Referral havolalar yaratish uchun node_id va kurslar ro'yxatini qaytaradi."""
        node = await self.get_mentor_node(mentor_user_id)
        if not node:
            return None
        courses = await self.course_repo.list_published()
        return node.id, courses

    async def get_mentor_card_status(self, mentor_user_id: int) -> dict[str, Any]:
        """Mentor kartasi va royalti to'lovlari holatini oladi."""
        from db.repositories.mentor_card_repo import MentorCardRepository
        from db.repositories.royalty_repo import RoyaltyLedgerRepository

        card_repo = MentorCardRepository(self.conn)
        royalty_repo = RoyaltyLedgerRepository(self.conn)

        card = await card_repo.get_active_card(mentor_user_id)
        node = await self.get_mentor_node(mentor_user_id)

        unsettled = None
        if node:
            unsettled = await royalty_repo.unsettled_info_for_child_node(node.id)

        return {
            "card": card,
            "node": node,
            "unsettled": unsettled,
        }

    async def approve_mentor_application(
        self, app_id: int
    ) -> tuple[Optional[MentorApplication], Optional[User]]:
        """Mentorlik arizasini tasdiqlaydi va 'payment_pending' holatiga o'tkazadi."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            return None, None
        await self.app_repo.update_status(app_id, "payment_pending")
        target_user = await self.user_repo.get_by_id(app.user_id)
        return app, target_user

    async def reject_mentor_application(
        self, app_id: int
    ) -> tuple[Optional[MentorApplication], Optional[User]]:
        """Mentorlik arizasini rad etadi va 'rejected' holatiga o'tkazadi."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            return None, None
        await self.app_repo.update_status(app_id, "rejected")
        target_user = await self.user_repo.get_by_id(app.user_id)
        return app, target_user

    async def approve_mentor_receipt(
        self, app_id: int
    ) -> Optional[dict[str, Any]]:
        """
        To'lov chekini tasdiqlaydi va nomzodni mentor qilib to'liq ochadi:
        1. Ariza holatini 'approved' qiladi
        2. User rolini 'mentor' qiladi
        3. Litsenziya tugunini faollashtiradi (yoki yaratadi)
        4. O'quv kabinetini yaratadi
        5. Barcha nashr qilingan kurslarga cheksiz ruxsat beradi
        Barchasi xavfsiz tranzaksiya ichida bajariladi.
        """
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            return None

        async with database.transaction():
            await self.app_repo.update_status(app_id, "approved")
            await self.user_repo.update_role(app.user_id, "mentor")

            node = await self.license_node_repo.get_by_owner_id(app.user_id)
            if not node:
                node_id = await self.license_node_repo.create_node(
                    owner_user_id=app.user_id,
                    course_id=1,
                    parent_id=1,
                    royalty_percent=20.0,
                    stage="limit",
                    status="active",
                )
            else:
                node_id = node.id
                await self.license_node_repo.update_status(node_id, "active")

            cabinet = await self.cabinet_service.get_or_create_for_node(node_id)

            all_courses = await self.course_repo.list_published()
            for course in all_courses:
                try:
                    await self.access_grant_repo.grant_course_access(
                        user_id=app.user_id,
                        course_id=course.id,
                        granted_via_sale_id=0,
                    )
                except Exception as c_ex:
                    logger.warning("Kurs %s ga ruxsat berishda xatolik: %s", course.id, c_ex)

            target_user = await self.user_repo.get_by_id(app.user_id)

        return {
            "app": app,
            "target_user": target_user,
            "cabinet": cabinet,
            "all_courses": all_courses,
            "node_id": node_id,
        }

    async def reject_mentor_receipt(
        self, app_id: int
    ) -> tuple[Optional[MentorApplication], Optional[User]]:
        """To'lov chekini rad etadi va 'receipt_rejected' holatiga o'tkazadi."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            return None, None
        await self.app_repo.update_status(app_id, "receipt_rejected")
        target_user = await self.user_repo.get_by_id(app.user_id)
        return app, target_user

    async def submit_receipt_photo(
        self, user_id: int, photo_id: str
    ) -> Optional[MentorApplication]:
        """Nomzod yuborgan to'lov cheki rasmini qabul qilib saqlaydi."""
        app = await self.app_repo.get_latest_by_user_id(user_id)
        if not app or app.status not in ("payment_pending", "receipt_rejected"):
            return None
        await self.app_repo.submit_receipt(app.id, photo_id)
        return await self.app_repo.get_by_id(app.id)
