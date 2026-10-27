from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.database import database
from db.repositories.user_repo import UserRepository
from db.repositories.waitlist_repo import WaitlistRepository
from db.repositories.notification_repo import NotificationRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["waitlist"])


class JoinWaitlistRequest(BaseModel):
    phone: str | None = None


@router.get("/{course_id}/waitlist")
async def get_course_waitlist_status(
    course_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = WaitlistRepository(conn)

    is_in = await repo.is_in_waitlist(course_id, user.id)
    count = await repo.get_count(course_id)

    return {
        "course_id": course_id,
        "is_in_waitlist": is_in,
        "waitlist_count": count,
    }


@router.post("/{course_id}/waitlist")
async def join_course_waitlist(
    course_id: int,
    body: JoinWaitlistRequest | None = None,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = WaitlistRepository(conn)
    notif_repo = NotificationRepository(conn)

    phone = (body.phone if body else None) or user.phone

    await repo.join_waitlist(course_id, user.id, phone)
    count = await repo.get_count(course_id)

    # Foydalanuvchiga tasdiqlovchi bildirishnoma yuborish
    try:
        await notif_repo.create_notification(
            user_id=user.id,
            type="system",
            title="AI Kursi Navbatiga yozildingiz! 🤖",
            message="Siz Sun'iy Intellekt (AI) kursi kutish ro'yxatiga (waitlist) muvaffaqiyatli qo'shildingiz. Kurs ochilishi bilan bot orqali sizga birinchi bo'lib xabar yuboramiz!",
            link=f"/course/{course_id}",
        )
    except Exception as e:
        logger.debug(f"Waitlist notification xatosi: {e}")

    return {
        "success": True,
        "message": "Siz muvaffaqiyatli navbatga yozildingiz!",
        "is_in_waitlist": True,
        "waitlist_count": count,
    }


@router.delete("/{course_id}/waitlist")
async def leave_course_waitlist(
    course_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = WaitlistRepository(conn)

    await repo.leave_waitlist(course_id, user.id)
    count = await repo.get_count(course_id)

    return {
        "success": True,
        "message": "Navbatdan chiqarildingiz",
        "is_in_waitlist": False,
        "waitlist_count": count,
    }
