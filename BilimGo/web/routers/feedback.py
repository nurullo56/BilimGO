from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.config import settings
from db.database import database
from db.repositories.feedback_repo import FeedbackRepository
from db.repositories.user_repo import UserRepository
from services.admin_notifier import admin_notifier
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

    # 🔔 Adminga xabarnoma yuborish (Topic 8: Mentorlar va o'quvchilar)
    stars = "⭐️" * payload.rating
    feedback_text = (
        f"💬 <b>Yangi fikr-mulohaza qoldirildi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.full_name or 'Talaba'} (ID: <code>{user.telegram_id}</code>)\n"
        f"🌟 <b>Baho:</b> {stars} ({payload.rating}/5)\n"
        f"📂 <b>Kategoriya:</b> {payload.category.title()}\n"
        f"📝 <b>Matn:</b>\n<i>{payload.comment.strip()}</i>"
    )
    import asyncio
    asyncio.create_task(admin_notifier.send_feedback_alert(feedback_text))
    return {
        "status": "success",
        "feedback_id": feedback_id,
        "message": "Fikringiz uchun rahmat! Fikr-mulohazangiz qabul qilindi.",
    }


@router.get("/admin/all")
async def get_all_feedbacks_for_admin(
    limit: int = 50,
    offset: int = 0,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict[str, Any]]:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    is_admin = user.role in ("admin", "super_mentor") or user.telegram_id in settings.bot.admin_ids
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat berilmagan")

    feedback_repo = FeedbackRepository(conn)
    return await feedback_repo.list_feedbacks(limit=limit, offset=offset)


@router.get("/my")
async def get_my_feedbacks(
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict[str, Any]]:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    feedback_repo = FeedbackRepository(conn)
    return await feedback_repo.get_user_feedbacks(user.id)
