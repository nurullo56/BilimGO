from __future__ import annotations

import html
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.config import settings
from db.database import database
from db.repositories.feedback_repo import FeedbackRepository
from db.repositories.user_repo import UserRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.lesson_repo import LessonRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5, default=5, description="1 dan 5 gacha baholash")
    comment: str = Field(min_length=3, max_length=2000, description="Fikr yoki taklif matni")
    category: str = Field(default="general", description="Kategoriya: general, lesson, suggestion, bug")
    course_id: int | None = None
    lesson_id: int | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreateRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict[str, Any]:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)
    feedback_repo = FeedbackRepository(conn)

    feedback_id = await feedback_repo.create_feedback(
        user_id=user.id,
        rating=payload.rating,
        comment=payload.comment.strip(),
        category=payload.category,
        course_id=payload.course_id,
        lesson_id=payload.lesson_id,
    )

    # Qo'shimcha ma'lumotlarni olish (Telegram xabari uchun)
    course_title = "Umumiy"
    lesson_title = None

    if payload.course_id:
        c = await CourseRepository(conn).get_by_id(payload.course_id)
        if c:
            course_title = c.title

    if payload.lesson_id:
        l = await LessonRepository(conn).get_by_id(payload.lesson_id)
        if l:
            lesson_title = l.title

    # Adminlarga yoki guruhga Telegram orqali xabarnoma yuborish
    try:
        stars = "⭐️" * max(1, min(5, payload.rating))
        student_name = html.escape(user.full_name or "Talaba")
        safe_comment = html.escape(payload.comment.strip())

        text_parts = [
            "💬 <b>Yangi o'quvchi fikr-mulohazasi (Feedback)!</b>\n",
            f"👤 <b>Talaba:</b> {student_name} (ID: <code>{user.telegram_id}</code>)",
            f"⭐ <b>Baho:</b> {stars} ({payload.rating}/5)",
            f"🏷 <b>Turi:</b> {payload.category}",
            f"📚 <b>Kurs:</b> {html.escape(course_title)}",
        ]
        if lesson_title:
            text_parts.append(f"📖 <b>Dars:</b> {html.escape(lesson_title)}")

        text_parts.append(f"\n📝 <b>Fikr:</b>\n<i>«{safe_comment}»</i>")

        telegram_msg = "\n".join(text_parts)

        # Adminlarga yuborish
        import httpx
        bot_url = f"https://api.telegram.org/bot{settings.bot.token}/sendMessage"
        recipients = list(settings.bot.admin_ids)
        if hasattr(settings, "super_mentor_group_id") and settings.super_mentor_group_id:
            recipients.append(settings.super_mentor_group_id)

        async with httpx.AsyncClient(timeout=5.0) as client:
            for recipient_id in recipients:
                try:
                    await client.post(
                        bot_url,
                        json={
                            "chat_id": recipient_id,
                            "text": telegram_msg,
                            "parse_mode": "HTML",
                        },
                    )
                except Exception as send_err:
                    logger.debug("Feedback telegram xabari yuborishda xatolik: %s", send_err)
    except Exception as e:
        logger.warning("Feedback bildirishnomasi tayyorlashda xatolik: %s", e)

    return {
        "status": "success",
        "feedback_id": feedback_id,
        "message": "Fikringiz uchun rahmat! Sizning fikringiz biz uchun juda muhim.",
    }


@router.get("/my")
async def get_my_feedbacks(
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict[str, Any]]:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    feedback_repo = FeedbackRepository(conn)
    return await feedback_repo.get_user_feedbacks(user.id)
