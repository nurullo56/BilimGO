from __future__ import annotations

import html
import logging

from db.repositories.completion_notification_repo import CompletionNotificationRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.engagement_repo import EngagementRepository, NudgeRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import UserRepository
from services.userbot_client import UserbotClient

logger = logging.getLogger(__name__)


class LessonCompletionService:
    def __init__(
        self,
        lesson_repo: LessonRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
        license_node_repo: LicenseNodeRepository,
        lesson_view_repo: LessonViewRepository,
        notification_repo: CompletionNotificationRepository,
        engagement_repo: EngagementRepository,
        nudge_repo: NudgeRepository,
        userbot_client: UserbotClient | None = None,
    ) -> None:
        self._lesson_repo = lesson_repo
        self._course_repo = course_repo
        self._user_repo = user_repo
        self._license_node_repo = license_node_repo
        self._lesson_view_repo = lesson_view_repo
        self._notification_repo = notification_repo
        self._engagement_repo = engagement_repo
        self._nudge_repo = nudge_repo
        self._userbot_client = userbot_client or UserbotClient()

    async def handle_lesson_progress(
        self,
        user_id: int,
        lesson_id: int,
        watch_duration_sec: int,
        completion_percent: int,
    ) -> bool:
        """Dars ko'rish progressini yangilaydi. Agar dars tugatilgan bo'lsa (completion_percent >= 90),
        avtomatik tarzda mentor userboti orqali o'quvchiga xabar yuboradi."""
        # 1. Talaba faolligini qayd etish va passivlik kampaniyasini to'xtatish
        await self._engagement_repo.touch(user_id)
        await self._nudge_repo.stop_campaign(user_id)

        # 2. Dars ko'rish progressini yozish
        # Agar user uchun dars ko'rish yozuvi bo'lmasa, yangi yaratish
        cursor = await self._lesson_view_repo._conn.execute(
            """
            SELECT id FROM lesson_views
            WHERE user_id = ? AND lesson_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, lesson_id),
        )
        row = await cursor.fetchone()
        if row:
            view_id = row["id"]
        else:
            view_id = await self._lesson_view_repo.start_view(user_id, lesson_id)

        completion_percent = max(0, min(100, completion_percent))
        await self._lesson_view_repo.update_progress(
            view_id=view_id,
            watch_duration_sec=watch_duration_sec,
            completion_percent=completion_percent,
        )

        is_completed = completion_percent >= 90
        if is_completed:
            await self._on_lesson_completed(user_id, lesson_id)

        return is_completed

    async def handle_lesson_completed(self, user_id: int, lesson_id: int) -> None:
        """Dars to'liq tugatilganda (masalan AI baholash orqali) chaqiriladi."""
        await self._engagement_repo.touch(user_id)
        await self._nudge_repo.stop_campaign(user_id)
        await self._on_lesson_completed(user_id, lesson_id)

    async def _on_lesson_completed(self, user_id: int, lesson_id: int) -> None:
        """Dars yakunlanganda o'quvchiga va mentorga xabarlarni yuborish."""
        # Qayta-qayta takroriy xabar yubormaslik uchun tekshirish
        already_notified = await self._notification_repo.is_notified(user_id, lesson_id)
        if already_notified:
            return

        user = await self._user_repo.get_by_id(user_id)
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not user or not lesson:
            return

        course = await self._course_repo.get_by_id(lesson.course_id)
        course_title = course.title if course else "Kurs"
        student_name = html.escape(user.full_name or "Hurmatli talaba")
        lesson_title = html.escape(lesson.title)

        # 1. O'quvchiga shaxsiy xabar (Userbot orqali, muvaffaqiyatsiz bo'lsa Bot API orqali)
        student_message = (
            f"Assalomu alaykum, <b>{student_name}</b>! 👏\n\n"
            f"<b>«{lesson_title}»</b> mavzusidagi darsni muvaffaqiyatli tugatganingiz bilan tabriklayman!\n\n"
            f"Qanday, darsda tushunmagan joylaringiz bo'ldimi? Amaliy topshiriqlarni ishlashga tayyormisiz?\n\n"
            f"Biror savolingiz yoki yordam kerak bo'lsa, bemalol shu yerga yozishingiz mumkin. O'rganishda davom eting! 🚀"
        )

        sent = await self._userbot_client.send_message(
            recipient_telegram_id=user.telegram_id,
            text=student_message,
        )

        if not sent:
            # Agar Userbot yubora olmasa, to'g'ridan-to'g'ri rasmiy Bot orqali yetkaziladi
            try:
                from core.config import settings
                import httpx
                bot_url = f"https://api.telegram.org/bot{settings.bot.token}/sendMessage"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        bot_url,
                        json={
                            "chat_id": user.telegram_id,
                            "text": student_message,
                            "parse_mode": "HTML",
                        },
                    )
                    sent = resp.status_code == 200
            except Exception as e:
                logger.error("Bot API fallback xatosi: %s", e)

        if sent:
            await self._notification_repo.mark_notified(user_id, lesson_id, status="sent")
            logger.info("O'quvchiga dars tugatish xabari yuborildi: user_id=%s, lesson_id=%s", user_id, lesson_id)
        else:
            await self._notification_repo.mark_notified(user_id, lesson_id, status="failed")
            logger.warning("O'quvchiga xabar yuborib bo'lmadi: user_id=%s, lesson_id=%s", user_id, lesson_id)

        # 2. Mentorga bildirishnoma (Dars tugatildi xabari)
        mentor_telegram_id = await self._find_mentor_telegram_id(course)
        if mentor_telegram_id and mentor_telegram_id != user.telegram_id:
            mentor_report = (
                f"ℹ️ <b>Dars yakunlandi!</b>\n\n"
                f"👤 <b>O'quvchi:</b> {student_name} (ID: <code>{user.telegram_id}</code>)\n"
                f"📚 <b>Kurs:</b> {html.escape(course_title)}\n"
                f"📖 <b>Dars:</b> {lesson_title}\n\n"
                f"✅ O'quvchiga darsni tugatganligi bo'yicha tabrik xabari yuborildi."
            )
            mentor_sent = await self._userbot_client.send_message(
                recipient_telegram_id=mentor_telegram_id,
                text=mentor_report,
            )
            if not mentor_sent:
                try:
                    from core.config import settings
                    import httpx
                    bot_url = f"https://api.telegram.org/bot{settings.bot.token}/sendMessage"
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        await client.post(
                            bot_url,
                            json={
                                "chat_id": mentor_telegram_id,
                                "text": mentor_report,
                                "parse_mode": "HTML",
                            },
                        )
                except Exception as exc:
                    import logging
                    logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    async def _find_mentor_telegram_id(self, course) -> int | None:
        if not course or not course.owner_node_id:
            return None
        node = await self._license_node_repo.get_by_id(course.owner_node_id)
        if not node:
            return None
        mentor_user = await self._user_repo.get_by_id(node.owner_user_id)
        return mentor_user.telegram_id if mentor_user else None
