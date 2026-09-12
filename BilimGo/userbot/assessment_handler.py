from __future__ import annotations

import logging
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.mentor_userbot_repo import MentorUserbotRepository
from db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

_ASSESS_COMMAND = re.compile(r"^/baholash\s+(\d+)$")

# chat_id (talaba bilan shaxsiy chat) -> kutilayotgan lesson_id
_pending_context: dict[int, int] = {}


async def handle_student_reply(
    *,
    user_repo: UserRepository,
    lesson_repo: LessonRepository,
    comprehension_repo: ComprehensionCheckRepository,
    mentor_userbot_id: int | None,
    student_telegram_id: int,
    lesson_id: int,
    raw_text: str,
) -> int | None:
    """Sof biznes-mantiq — Telegram'dan mustaqil, test qilinadigan qism."""
    lesson = await lesson_repo.get_by_id(lesson_id)
    if lesson is None:
        logger.warning("Noma'lum lesson_id=%s, e'tiborga olinmadi", lesson_id)
        return None

    student = await user_repo.get_or_create(telegram_id=student_telegram_id)

    check_id = await comprehension_repo.create_pending(
        student_id=student.id,
        lesson_id=lesson_id,
        raw_response=raw_text,
        mentor_userbot_id=mentor_userbot_id,
    )
    return check_id


def build_assessment_handlers(client: Client, db_conn, mentor_userbot_id: int | None) -> None:
    user_repo = UserRepository(db_conn)
    lesson_repo = LessonRepository(db_conn)
    comprehension_repo = ComprehensionCheckRepository(db_conn)

    @client.on_message(filters.private & filters.outgoing & filters.text)
    async def on_mentor_command(_: Client, message: Message) -> None:
        match = _ASSESS_COMMAND.match(message.text.strip())
        if not match:
            return
        lesson_id = int(match.group(1))
        _pending_context[message.chat.id] = lesson_id
        logger.info("Baholash konteksti o'rnatildi: chat=%s lesson=%s", message.chat.id, lesson_id)

    @client.on_message(filters.private & filters.incoming & filters.text)
    async def on_student_reply(_: Client, message: Message) -> None:
        lesson_id = _pending_context.pop(message.chat.id, None)
        
        # Agar mentor kontekst o'rnatmagan bo'lsa, talabaning eng oxirgi ko'rgan darsini bazadan qidiramiz
        if lesson_id is None:
            cursor = await db_conn.execute(
                """
                SELECT lv.lesson_id
                FROM lesson_views lv
                JOIN users u ON u.id = lv.user_id
                WHERE u.telegram_id = ?
                ORDER BY lv.id DESC LIMIT 1
                """,
                (message.from_user.id,),
            )
            row = await cursor.fetchone()
            if row:
                lesson_id = row["lesson_id"]

        if lesson_id is None:
            return

        lesson = await lesson_repo.get_by_id(lesson_id)
        lesson_title = f" «{lesson.title}»" if lesson else ""

        check_id = await handle_student_reply(
            user_repo=user_repo,
            lesson_repo=lesson_repo,
            comprehension_repo=comprehension_repo,
            mentor_userbot_id=mentor_userbot_id,
            student_telegram_id=message.from_user.id,
            lesson_id=lesson_id,
            raw_text=message.text,
        )
        if check_id is not None:
            await message.reply_text(
                f"✍️{lesson_title} darsi bo'yicha javobingiz qabul qilindi. AI tomonidan tahlil qilinmoqda..."
            )
