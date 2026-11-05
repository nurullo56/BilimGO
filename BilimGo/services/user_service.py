from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
from typing import Any
from urllib.parse import parse_qsl

from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.mentor_application_repo import MentorApplicationRepository
from db.repositories.user_repo import User, UserRepository
from services.admin_notifier import admin_notifier

logger = logging.getLogger(__name__)

MONTHS_UZ = {
    1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel",
    5: "may", 6: "iyun", 7: "iyul", 8: "avgust",
    9: "sentabr", 10: "oktabr", 11: "noyabr", 12: "dekabr"
}


def format_uzbek_dt(raw_dt: str | None = None) -> str:
    """Sana va vaqtni o'zbek tilidagi chiroyli ko'rinishga formatlaydi."""
    if not raw_dt:
        now = datetime.datetime.now()
        return f"{now.day}-{MONTHS_UZ.get(now.month, '')} {now.year}-yil, {now.strftime('%H:%M')}"
    try:
        clean_str = raw_dt.replace("T", " ")[:19]
        dt = datetime.datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        return f"{dt.day}-{MONTHS_UZ.get(dt.month, '')} {dt.year}-yil, {dt.strftime('%H:%M')}"
    except Exception:
        return raw_dt[:16] if raw_dt else "Noma'lum"


class UserService:
    def __init__(
        self,
        user_repo: UserRepository | None = None,
        access_grant_repo: AccessGrantRepository | None = None,
        lesson_view_repo: LessonViewRepository | None = None,
        license_node_repo: LicenseNodeRepository | None = None,
        mentor_app_repo: MentorApplicationRepository | None = None,
        conn: Any = None,
    ) -> None:
        c = conn or database.conn
        self.user_repo = user_repo or UserRepository(c)
        self.access_grant_repo = access_grant_repo or AccessGrantRepository(c)
        self.lesson_view_repo = lesson_view_repo or LessonViewRepository(c)
        self.license_node_repo = license_node_repo or LicenseNodeRepository(c)
        self.mentor_app_repo = mentor_app_repo or MentorApplicationRepository(c)

    @classmethod
    def create_default(cls, conn=None) -> "UserService":
        """Yagona markazlashgan UserService fabrikasi."""
        c = conn or database.conn
        return cls(
            user_repo=UserRepository(c),
            access_grant_repo=AccessGrantRepository(c),
            lesson_view_repo=LessonViewRepository(c),
            license_node_repo=LicenseNodeRepository(c),
            mentor_app_repo=MentorApplicationRepository(c),
        )

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.user_repo.get_by_id(user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.user_repo.get_by_telegram_id(telegram_id)

    async def get_or_create(self, telegram_id: int, full_name: str | None = None) -> User:
        return await self.user_repo.get_or_create(telegram_id=telegram_id, full_name=full_name)

    async def get_user_profile(self, user_id: int) -> dict[str, Any] | None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return dict(user)

    async def update_user_status(self, user_id: int, status: str) -> None:
        await self.user_repo.set_status(user_id, status)

    async def update_role(self, user_id: int, role: str) -> None:
        await self.user_repo.update_role(user_id, role)

    async def update_profile(
        self, user_id: int, full_name: str | None = None, phone: str | None = None
    ) -> None:
        """Foydalanuvchi profilini (ism va telefon) yangilaydi."""
        await self.user_repo.update_profile(user_id=user_id, full_name=full_name, phone=phone)

    async def get_full_profile(
        self,
        telegram_id: int,
        x_telegram_init_data: str | None = None,
        tg_info: dict | None = None,
        admin_ids: list[int] | None = None,
    ) -> dict:
        """Foydalanuvchi profilini barcha statistika va ko'rsatkichlar bilan to'liq shakllantiradi."""
        tg_info = tg_info or {}
        admin_ids = admin_ids or []
        user = await self.user_repo.get_or_create(telegram_id=telegram_id)

        # 1. InitData dan username va photo_url ni olish
        init_username = None
        init_photo_url = None
        if x_telegram_init_data:
            try:
                pairs = dict(parse_qsl(x_telegram_init_data, strict_parsing=False))
                user_raw = pairs.get("user")
                if user_raw:
                    user_obj = json.loads(user_raw)
                    init_username = user_obj.get("username")
                    init_photo_url = user_obj.get("photo_url")
            except Exception as exc:
                logger.warning(f"InitData parsing error: {exc}")

        resolved_username = (
            init_username
            or tg_info.get("username")
            or (f"user_{user.telegram_id}" if not user.full_name else user.full_name.lower().replace(" ", "_"))
        )
        clean_username = f"@{resolved_username.lstrip('@')}"

        # 2. Avatar URL
        avatar_url = ""
        if tg_info.get("photo_bytes"):
            avatar_url = f"/api/users/{user.telegram_id}/avatar"
        elif init_photo_url:
            avatar_url = init_photo_url
        elif tg_info.get("photo_url"):
            avatar_url = tg_info.get("photo_url")

        # 3. Foydalanuvchi ismini yangilash
        name_parts = (user.full_name or "").split(" ", 1)
        first_name = name_parts[0] if name_parts and name_parts[0] else (tg_info.get("first_name") or "Foydalanuvchi")
        last_name = name_parts[1] if len(name_parts) > 1 else (tg_info.get("last_name") or "")

        if (not user.full_name or user.full_name == "Foydalanuvchi") and tg_info.get("first_name"):
            first_name = tg_info.get("first_name") or "Foydalanuvchi"
            last_name = tg_info.get("last_name") or ""
            updated_full_name = f"{first_name} {last_name}".strip()
            await self.user_repo.update_profile(user.id, full_name=updated_full_name)

        # 4. Rolni aniqlash
        role = user.role
        if telegram_id in admin_ids or user.role == "admin":
            role = "super_mentor"
        elif user.role == "mentor":
            role = "mentor"
        else:
            node = await self.license_node_repo.get_by_owner_id(user.id)
            role = "mentor" if node else "student"

        # 5. O'quvchi statistikasi
        enrolled_count = await self.access_grant_repo.count_active_courses(user.id)
        stats = await self.lesson_view_repo.get_user_study_stats(user.id)
        streak_days = await self.lesson_view_repo.get_streak_days(user.id)
        act_rows = await self.lesson_view_repo.get_daily_activity_map(user.id, days=30)

        # 6. Oxirgi 14 kunlik faollik xaritasi
        today = datetime.date.today()
        uzbek_day_names = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
        daily_activity = []

        for i in range(13, -1, -1):
            d = today - datetime.timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            act = act_rows.get(d_str)
            mins = round((act["total_sec"] if act else 0) / 60)
            views = act["views_count"] if act else 0
            is_today = (i == 0)
            is_active = (mins > 0 or views > 0)

            if mins >= 60:
                h = "h-14"
            elif mins >= 30:
                h = "h-12"
            elif mins >= 15:
                h = "h-10"
            elif mins > 0 or views > 0:
                h = "h-8"
            else:
                h = "h-6"

            daily_activity.append({
                "date": d_str,
                "day_label": uzbek_day_names[d.weekday()],
                "formatted_date": f"{d.day:02d}.{d.month:02d}",
                "minutes": mins,
                "views_count": views,
                "active": is_active,
                "height": h,
                "is_today": is_today,
            })

        completed_lessons = stats["completed_lessons"]

        return {
            "id": f"u-{user.id}",
            "telegram_id": user.telegram_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": clean_username,
            "phone": user.phone or "+998 90 000 00 00",
            "avatar": avatar_url,
            "role": role,
            "is_admin": (telegram_id in admin_ids) or (user.role == "admin"),
            "assigned_mentor_id": "mentor-1",
            "enrolled_courses_count": enrolled_count,
            "completed_lessons_count": completed_lessons,
            "total_study_time_minutes": stats["total_study_minutes"],
            "streak_days": max(1, streak_days),
            "joined_date": user.created_at[:10] if user.created_at else "2026",
            "wallet_balance": 0,
            "certificate_count": 1 if completed_lessons >= 10 else 0,
            "daily_activity": daily_activity,
        }

    async def update_profile_info(
        self,
        telegram_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        role: str | None = None,
        admin_ids: list[int] | None = None,
    ) -> None:
        """Foydalanuvchi ma'lumotlarini (ism, telefon, rol) yangilaydi."""
        admin_ids = admin_ids or []
        user = await self.user_repo.get_or_create(telegram_id=telegram_id)

        full_name = None
        if first_name or last_name:
            parts = []
            if first_name:
                parts.append(first_name)
            if last_name:
                parts.append(last_name)
            full_name = " ".join(parts)

        if full_name or phone:
            await self.user_repo.update_profile(user.id, full_name=full_name, phone=phone)

        if role and role in ["student", "mentor", "admin"]:
            if telegram_id in admin_ids:
                await self.user_repo.update_role(user.id, role)

    async def list_mentors_directory(self) -> list[dict]:
        """Barcha mentorlar ro'yxatini qaytaradi."""
        rows = await self.user_repo.list_mentors_with_nodes()
        results = []
        for r in rows:
            results.append({
                "id": f"mentor-{r['id']}",
                "name": r["full_name"] or f"Mentor #{r['id']}",
                "username": f"id{r['telegram_id']}",
                "avatar": "👨‍🏫",
                "tier": r["stage"],
                "total_students": 12,
                "rating": 4.9,
            })
        if not results:
            results = [
                {
                    "id": "mentor-1",
                    "name": "Nurulloh (Bosh Mentor)",
                    "username": "@nurulloh_bilimgo",
                    "avatar": "👑",
                    "tier": "stage_3",
                    "total_students": 45,
                    "rating": 5.0,
                }
            ]
        return results

    async def create_mentor_application(
        self,
        telegram_id: int,
        full_name: str,
        phone: str,
        course_direction: str,
        experience_bio: str,
        telegram_username: str | None = None,
    ) -> dict:
        """Yangi mentorlik arizasini saqlaydi va adminga formatlangan xabarnoma yuboradi."""
        user = await self.user_repo.get_or_create(telegram_id=telegram_id)

        app_id = await self.mentor_app_repo.create(
            user_id=user.id,
            full_name=full_name,
            phone=phone,
            course_direction=course_direction,
            experience_bio=experience_bio,
            telegram_username=telegram_username,
        )

        mentor_info = await self.user_repo.get_user_assigned_mentor_and_cabinet(user.id)
        if mentor_info:
            mentor_display = f"{mentor_info['mentor_name']} (ID: <code>{mentor_info['mentor_tg_id']}</code>)"
            cabinet_display = mentor_info["cabinet_name"]
        else:
            mentor_display = "To'g'ridan-to'g'ri (Platforma)"
            cabinet_display = "Hali biriktirilmagan"

        course_title = await self.access_grant_repo.get_latest_active_course_title(user.id)
        enrolled_course_display = course_title or "Hozircha kurs yo'q"

        registered_time_display = format_uzbek_dt(user.created_at)
        submission_time_display = format_uzbek_dt()

        tg_user_link = f"@{telegram_username.lstrip('@')}" if telegram_username else f"ID: {user.telegram_id}"
        admin_notify_text = (
            f"👨‍🏫 <b>YANGI MENTORLIK ARIZASI!</b>\n\n"
            f"🆔 <b>Ariza raqami:</b> #{app_id}\n"
            f"👤 <b>F.I.SH:</b> <b>{full_name}</b>\n"
            f"📱 <b>Telefon:</b> <code>{phone}</code>\n"
            f"💬 <b>Telegram:</b> {tg_user_link} (<code>{user.telegram_id}</code>)\n\n"
            f"🎯 <b>Ariza yo'nalishi:</b> {course_direction}\n"
            f"📝 <b>Tajriba / Ma'lumot:</b>\n<i>{experience_bio}</i>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>PLATFORMA MA'LUMOTLARI:</b>\n"
            f"📅 <b>Platformaga a'zo bo'lgan:</b> {registered_time_display}\n"
            f"👑 <b>Biriktirilgan Mentori:</b> {mentor_display}\n"
            f"👥 <b>Biriktirilgan Guruhi:</b> {cabinet_display}\n"
            f"📚 <b>O'qiyotgan kursi:</b> {enrolled_course_display}\n\n"
            f"⏰ <b>Ariza berilgan vaqt:</b> {submission_time_display}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚡️ <i>Iltimos, arizani ko'rib chiqing va tasdiqlang.</i>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Tasdiqlash", "callback_data": f"mentor_app:approve:{app_id}"},
                    {"text": "❌ Rad etish", "callback_data": f"mentor_app:reject:{app_id}"},
                ]
            ]
        }
        asyncio.create_task(admin_notifier.send_mentor_application(admin_notify_text, reply_markup=reply_markup))

        return {
            "success": True,
            "message": "Arizangiz muvaffaqiyatli qabul qilindi!",
            "application_id": app_id,
        }

    async def get_my_mentor_application(self, telegram_id: int) -> dict:
        """Foydalanuvchining oxirgi mentorlik arizasini qaytaradi."""
        user = await self.user_repo.get_or_create(telegram_id=telegram_id)
        app = await self.mentor_app_repo.get_latest_by_user_id(user.id)
        default_price = int(os.getenv("MENTOR_PRICE", "949000"))
        card_number = os.getenv("MENTOR_CARD_NUMBER", "8600 0000 0000 0000")
        card_holder = os.getenv("MENTOR_CARD_HOLDER", "Admin")

        if not app:
            return {
                "application": None,
                "payment_amount": default_price,
                "admin_card_number": card_number,
                "admin_card_holder": card_holder,
            }

        app_data = {
            "id": app.id,
            "full_name": app.full_name,
            "phone": app.phone,
            "telegram_username": app.telegram_username,
            "course_direction": app.course_direction,
            "experience_bio": app.experience_bio,
            "status": app.status,
            "payment_amount": app.payment_amount or default_price,
            "receipt_photo_id": app.receipt_photo_id,
            "created_at": app.created_at,
            "admin_card_number": card_number,
            "admin_card_holder": card_holder,
        }
        return {
            "application": app_data,
            **app_data,
        }

    async def submit_mentor_application_receipt(
        self,
        telegram_id: int,
        application_id: int,
        receipt_photo_id: str,
    ) -> dict:
        """To'lov chekini qabul qiladi va adminga chek tasdiqlash xabarnomasini yuboradi."""
        user = await self.user_repo.get_or_create(telegram_id=telegram_id)
        app = await self.mentor_app_repo.get_by_id(application_id)
        if not app or app.user_id != user.id:
            raise ValueError("Ariza topilmadi")

        await self.mentor_app_repo.submit_receipt(application_id, receipt_photo_id)

        receipt_notify_text = (
            f"🧾 <b>MENTORLIK TO'LOV CHEKI YUBORILDI!</b>\n\n"
            f"🆔 <b>Ariza raqami:</b> #{application_id}\n"
            f"👤 <b>Nomzod:</b> <b>{app.full_name}</b>\n"
            f"📱 <b>Telefon:</b> <code>{app.phone}</code>\n"
            f"💬 <b>Telegram:</b> {app.telegram_username or f'ID: {user.telegram_id}'}\n"
            f"💰 <b>To'lov summasi:</b> {app.payment_amount:,} so'm\n"
            f"🖼 <b>Chek fayl ID:</b> <code>{receipt_photo_id}</code>\n\n"
            f"⚡️ <i>Iltimos, to'lovni tekshirib arizani tasdiqlang.</i>"
        )

        receipt_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Chekni tasdiqlash", "callback_data": f"mentor_receipt:approve:{application_id}"},
                    {"text": "❌ Rad etish", "callback_data": f"mentor_receipt:reject:{application_id}"},
                ]
            ]
        }
        asyncio.create_task(
            admin_notifier.send_payment_receipt(
                receipt_photo_id, receipt_notify_text, reply_markup=receipt_markup
            )
        )

        return {
            "success": True,
            "message": "Chek muvaffaqiyatli yuborildi!",
        }
