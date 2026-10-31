from __future__ import annotations

import html
import logging
from typing import Any
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.config import settings
from db.database import database
from db.repositories.notification_repo import NotificationRepository
from db.repositories.user_repo import UserRepository
from db.repositories.waitlist_repo import WaitlistRepository
from services.admin_notifier import admin_notifier
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["waitlist"])


class JoinWaitlistRequest(BaseModel):
    phone: str | None = None


class WaitlistBroadcastRequest(BaseModel):
    text: str


async def _send_telegram_msg(chat_id: int, text: str, reply_markup: dict | None = None) -> bool:
    """Telegram Bot API orqali xabar yuborish yordamchisi."""
    if not settings.bot.token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.bot.token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Telegram xabar yuborishda xatolik (%s): %s", chat_id, exc)
        return False


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

    # 1. Mini App ichki bildirishnomasi
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

    # 2. Foydalanuvchining shaxsiy Telegramiga tasdiqlovchi xabar yuborish
    user_name = html.escape(user.full_name or "Do'stim")
    user_msg = (
        f"🤖 <b>Sun'iy Intellekt (AI) kursi navbatiga yozildingiz!</b>\n\n"
        f"Hurmatli <b>{user_name}</b>, siz Sun'iy Intellekt (AI) kursi kutish roʻyxatiga (Waitlist) muvaffaqiyatli qoʻshildingiz! 🎉\n\n"
        f"📌 <b>Kurs:</b> Sun'iy Intellekt (AI) Asoslari\n"
        f"📊 <b>Sizning navbatingiz:</b> #{count}-oʻrin\n"
        f"⏳ <b>Holat:</b> Darslar yakuniy tahrirda va tez kunda eʼlon qilinadi.\n\n"
        f"Kurs ochilishi bilan sizga bot orqali maxsus chegirma va taklif bilan xabar yuboramiz! 🚀"
    )
    if user.telegram_id:
        await _send_telegram_msg(user.telegram_id, user_msg)

    # 3. Administratorlarga yangi navbat haqida ogohlantirish yuborish (Topic 8: Mentorlar va o'quvchilar)
    admin_msg = (
        f"📋 <b>Yangi o'quvchi AI kursi navbatiga yozildi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user_name} (ID: <code>{user.telegram_id}</code>)\n"
        f"📱 <b>Telefon:</b> <code>{phone or 'Kiritilmagan'}</code>\n"
        f"📊 <b>Jami navbatdagilar:</b> <b>{count} ta</b>"
    )
    await admin_notifier.send_waitlist_alert(admin_msg)

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

    # Foydalanuvchiga Telegramda bekor qilinganini bildirish
    user_msg = (
        f"ℹ️ <b>Kutish ro'yxatidan chiqarildingiz.</b>\n\n"
        f"Siz Sun'iy Intellekt (AI) kursi navbatidan muvaffaqiyatli chiqdingiz. "
        f"Istalgan vaqtda qayta navbatga yozilishingiz mumkin."
    )
    if user.telegram_id:
        await _send_telegram_msg(user.telegram_id, user_msg)

    return {
        "success": True,
        "message": "Navbatdan chiqarildingiz",
        "is_in_waitlist": False,
        "waitlist_count": count,
    }


@router.get("/{course_id}/waitlist/users")
async def list_course_waitlist_users(
    course_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict]:
    """Adminlar uchun: Navbatda turgan barcha foydalanuvchilar ro'yxati."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    is_admin = telegram_id in settings.bot.admin_ids or user.role in ("admin", "super_mentor")
    if not is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Faqat adminlar uchun ruxsat berilgan")

    repo = WaitlistRepository(conn)
    return await repo.get_waitlist_users(course_id)


@router.post("/{course_id}/waitlist/broadcast")
async def broadcast_to_waitlist_users(
    course_id: int,
    body: WaitlistBroadcastRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """Adminlar uchun: Kurs ochilganda barcha navbatdagilarga e'lon xabarini tarqatish."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    is_admin = telegram_id in settings.bot.admin_ids or user.role in ("admin", "super_mentor")
    if not is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Faqat adminlar uchun ruxsat berilgan")

    repo = WaitlistRepository(conn)
    users = await repo.get_waitlist_users(course_id)

    sent = 0
    failed = 0
    for u in users:
        tg_id = u.get("telegram_id")
        if tg_id:
            ok = await _send_telegram_msg(tg_id, body.text)
            if ok:
                sent += 1
            else:
                failed += 1

    return {
        "success": True,
        "total": len(users),
        "sent": sent,
        "failed": failed,
    }
