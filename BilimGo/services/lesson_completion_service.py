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

        # 3. Kursning 1-darsini ko'rishni boshlaganda faqat 1 ta xabar yuborish
        await self._check_and_notify_course_started(user_id, lesson_id)

        is_completed = completion_percent >= 90
        if is_completed:
            # 4. Faqat kursning eng oxirgi darsi tugatilganda 1 ta tabrik xabari yuborish
            await self._check_and_notify_course_completed(user_id, lesson_id)

        return is_completed

    async def handle_lesson_completed(self, user_id: int, lesson_id: int) -> None:
        """Dars to'liq tugatilganda (masalan AI baholash orqali) chaqiriladi."""
        await self._engagement_repo.touch(user_id)
        await self._nudge_repo.stop_campaign(user_id)
        await self._check_and_notify_course_completed(user_id, lesson_id)

    async def _send_direct_message(self, recipient_telegram_id: int, text: str) -> bool:
        """Userbot orqali yoki bot API fallback orqali xabar yuborish."""
        sent = await self._userbot_client.send_message(
            recipient_telegram_id=recipient_telegram_id,
            text=text,
        )
        if not sent:
            try:
                from core.config import settings
                import httpx
                bot_url = f"https://api.telegram.org/bot{settings.bot.token}/sendMessage"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        bot_url,
                        json={
                            "chat_id": recipient_telegram_id,
                            "text": text,
                            "parse_mode": "HTML",
                        },
                    )
                    sent = resp.status_code == 200
            except Exception as e:
                logger.error("Bot API fallback xatosi: %s", e)
        return sent

    async def _check_and_notify_course_started(self, user_id: int, lesson_id: int) -> None:
        """Kursning 1-darsi boshlanganda o'quvchiga faqat 1 marta xabar yuborish."""
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not lesson:
            return

        course_id = lesson.course_id
        lessons = await self._lesson_repo.list_by_course(course_id)
        if not lessons:
            return

        # Faqat eng birinchi dars (eng kichik order_index) boshlanganda
        first_lesson = lessons[0]
        if lesson.id != first_lesson.id:
            return

        # Parallel so'rovlar to'qnashmasligi uchun atomik bron qilish
        claimed = await self._notification_repo.try_claim_course_notification(
            user_id=user_id,
            course_id=course_id,
            notification_type="started",
        )
        if not claimed:
            return

        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.telegram_id:
            return

        course = await self._course_repo.get_by_id(course_id)
        course_title = course.title if course else "Kurs"
        student_name = html.escape(user.full_name or "Hurmatli talaba")

        start_message = (
            f"Assalomu alaykum, <b>{student_name}</b>! 👏\n\n"
            f"<b>«{html.escape(course_title)}»</b> kursini o'rganishni boshlaganingiz bilan qutlayman! 🚀\n\n"
            f"Darslarni muntazam o'rganib boring va amaliyotda qo'llang. "
            f"Biror savolingiz yoki yordam kerak bo'lsa, bemalol shu yerga yozishingiz mumkin.\n\n"
            f"O'rganishda omad tilaymiz! 💪"
        )

        sent = await self._send_direct_message(user.telegram_id, start_message)
        status = "sent" if sent else "failed"
        await self._notification_repo.mark_course_notified(
            user_id=user_id,
            course_id=course_id,
            notification_type="started",
            status=status,
        )
        if sent:
            logger.info("O'quvchiga kurs boshlanishi xabari yuborildi: user_id=%s, course_id=%s", user_id, course_id)

    async def _check_and_notify_course_completed(self, user_id: int, lesson_id: int) -> None:
        """Kursning eng oxirgi darsi tugatilganda o'quvchi va mentorga faqat 1 marta tabrik xabari yuborish."""
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not lesson:
            return

        course_id = lesson.course_id
        lessons = await self._lesson_repo.list_by_course(course_id)
        if not lessons:
            return

        # Faqat eng oxirgi dars (eng katta order_index) tugatilganda
        last_lesson = lessons[-1]
        if lesson.id != last_lesson.id:
            # Oraliq darslar tugaganda xabar yuborilmaydi
            return

        # Parallel so'rovlar to'qnashmasligi uchun atomik bron qilish
        claimed = await self._notification_repo.try_claim_course_notification(
            user_id=user_id,
            course_id=course_id,
            notification_type="completed",
        )
        if not claimed:
            return

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return

        course = await self._course_repo.get_by_id(course_id)
        course_title = course.title if course else "Kurs"
        student_name = html.escape(user.full_name or "Hurmatli talaba")

        # 1. O'quvchiga yakuniy tabrik xabari
        completed_message = (
            f"Assalomu alaykum, <b>{student_name}</b>! 🎉\n\n"
            f"<b>«{html.escape(course_title)}»</b> kursining barcha darslarini muvaffaqiyatli tugatganingiz bilan chin dildan tabriklayman! 👏\n\n"
            f"Siz kursni to'liq yakunladingiz. O'rgangan bilimlaringiz amaliyotda sizga ulkan yutuqlar olib kelsin!\n\n"
            f"Kelgusi faoliyatingizda muvaffaqiyatlar tilaymiz! 🚀"
        )

        sent = await self._send_direct_message(user.telegram_id, completed_message)
        status = "sent" if sent else "failed"
        await self._notification_repo.mark_course_notified(
            user_id=user_id,
            course_id=course_id,
            notification_type="completed",
            status=status,
        )

        if sent:
            logger.info("O'quvchiga kurs yakunlanishi xabari yuborildi: user_id=%s, course_id=%s", user_id, course_id)

        # 2. Mentorga bildirishnoma
        mentor_telegram_id = await self._find_mentor_telegram_id(course)
        if mentor_telegram_id and mentor_telegram_id != user.telegram_id:
            mentor_report = (
                f"🎉 <b>Kurs yakunlandi!</b>\n\n"
                f"👤 <b>O'quvchi:</b> {student_name} (ID: <code>{user.telegram_id}</code>)\n"
                f"📚 <b>Kurs:</b> {html.escape(course_title)}\n\n"
                f"✅ O'quvchi kursning barcha darslarini to'liq yakunladi va tabrik xabari yuborildi."
            )
            await self._send_direct_message(mentor_telegram_id, mentor_report)

    async def _find_mentor_telegram_id(self, course) -> int | None:
        if not course or not course.owner_node_id:
            return None
        node = await self._license_node_repo.get_by_id(course.owner_node_id)
        if not node:
            return None
        mentor_user = await self._user_repo.get_by_id(node.owner_user_id)
        return mentor_user.telegram_id if mentor_user else None
