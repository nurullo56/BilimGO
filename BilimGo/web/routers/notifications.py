from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from db.database import database
from db.repositories.notification_repo import NotificationRepository
from db.repositories.user_repo import UserRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = NotificationRepository(conn)

    notifications = await repo.get_user_notifications(user.id, limit=40)

    # Agar foydalanuvchida hali xabarnomalar bo'lmasa, dastlabki foydali xabarlarni yaratamiz
    if not notifications:
        await repo.create_notification(
            user_id=user.id,
            type="system",
            title="BilimGo platformasiga xush kelibsiz! 🎉",
            message="O'quv jarayonidagi barcha yangiliklar, baholar va eslatmalar shu yerda ko'rinadi.",
            link=None,
        )
        await repo.create_notification(
            user_id=user.id,
            type="ai_evaluation",
            title="AI Baholash va Testlar faol 🤖",
            message="Darslar yakunida savollarga javob bering va AI o'qituvchidan tezkor fikr-mulohaza oling.",
            link=None,
        )
        if user.role in ("mentor", "super_mentor"):
            await repo.create_notification(
                user_id=user.id,
                type="mentor",
                title="Mentorlik Kabineti faol 🎓",
                message="Shogirdlaringiz faolligini nazorat qiling va guruhlarga e'lonlar yuboring.",
                link="/cabinet",
            )
        notifications = await repo.get_user_notifications(user.id, limit=40)

    unread_count = await repo.get_unread_count(user.id)
    return {
        "notifications": notifications,
        "unread_count": unread_count,
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = NotificationRepository(conn)

    success = await repo.mark_as_read(notification_id, user.id)
    unread_count = await repo.get_unread_count(user.id)
    return {
        "success": success,
        "unread_count": unread_count,
    }


@router.post("/read-all")
async def mark_all_read(
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = NotificationRepository(conn)

    updated_count = await repo.mark_all_as_read(user.id)
    return {
        "success": True,
        "updated_count": updated_count,
        "unread_count": 0,
    }
