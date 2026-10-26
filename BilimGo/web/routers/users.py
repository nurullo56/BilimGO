from __future__ import annotations

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.config import settings
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import UserRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["users"])


class UserProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str | None = None


import time
from urllib.parse import parse_qsl
import httpx
from fastapi import Header, Response

_USER_CACHE: dict[int, dict] = {}


async def _fetch_telegram_user_info(telegram_id: int) -> dict:
    """Telegram Bot API orqali foydalanuvchining real username va oxirgi profil rasmini oladi."""
    now = time.time()
    cached = _USER_CACHE.get(telegram_id)
    if cached and (now - cached.get("_cached_at", 0) < 600):
        return cached

    token = settings.bot.token
    info: dict = {
        "username": None,
        "first_name": None,
        "last_name": None,
        "photo_url": None,
        "photo_bytes": None,
        "_cached_at": now,
    }

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            # 1. Get Chat info for real username
            r_chat = await client.get(
                f"https://api.telegram.org/bot{token}/getChat",
                params={"chat_id": telegram_id},
            )
            if r_chat.is_success:
                chat_data = r_chat.json().get("result", {})
                if chat_data.get("username"):
                    info["username"] = chat_data["username"]
                if chat_data.get("first_name"):
                    info["first_name"] = chat_data["first_name"]
                if chat_data.get("last_name"):
                    info["last_name"] = chat_data["last_name"]

            # 2. Get latest profile photo
            r_photos = await client.get(
                f"https://api.telegram.org/bot{token}/getUserProfilePhotos",
                params={"user_id": telegram_id, "limit": 1},
            )
            if r_photos.is_success:
                photos_data = r_photos.json().get("result", {})
                photos = photos_data.get("photos", [])
                if photos and len(photos) > 0:
                    # Eng katta sifatdagi rasmni tanlaymiz
                    best_photo = photos[0][-1]
                    file_id = best_photo["file_id"]

                    r_file = await client.get(
                        f"https://api.telegram.org/bot{token}/getFile",
                        params={"file_id": file_id},
                    )
                    if r_file.is_success:
                        file_path = r_file.json().get("result", {}).get("file_path")
                        if file_path:
                            photo_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                            info["photo_url"] = photo_url

                            # Rasmni yuklab keshga olamiz
                            r_img = await client.get(photo_url)
                            if r_img.is_success:
                                info["photo_bytes"] = r_img.content
    except Exception as exc:
        logger.warning(f"Telegram user info fetch error for {telegram_id}: {exc}")

    _USER_CACHE[telegram_id] = info
    return info


@router.get("/users/{telegram_id}/avatar")
async def get_user_avatar(telegram_id: int):
    """Foydalanuvchining Telegramdagi oxirgi profil rasmini uzatadi."""
    info = await _fetch_telegram_user_info(telegram_id)
    photo_bytes = info.get("photo_bytes")
    if photo_bytes:
        return Response(
            content=photo_bytes,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    raise HTTPException(status_code=404, detail="Avatar topilmadi")


@router.get("/users/profile")
async def get_user_profile(
    telegram_id: int = Depends(get_current_telegram_id),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    # Telegram Bot API dan haqiqiy ma'lumotlarni tekshiramiz
    tg_info = await _fetch_telegram_user_info(telegram_id)

    # Agar initData yuborilgan bo'lsa, undagi user ma'lumotlarini ham olamiz
    init_username = None
    init_photo_url = None
    if x_telegram_init_data:
        try:
            import json
            pairs = dict(parse_qsl(x_telegram_init_data, strict_parsing=False))
            user_raw = pairs.get("user")
            if user_raw:
                user_obj = json.loads(user_raw)
                init_username = user_obj.get("username")
                init_photo_url = user_obj.get("photo_url")
        except Exception as exc:
            import logging
            logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    resolved_username = (
        init_username
        or tg_info.get("username")
        or (f"user_{user.telegram_id}" if not user.full_name else user.full_name.lower().replace(" ", "_"))
    )
    clean_username = f"@{resolved_username.lstrip('@')}"

    # Avatar URL
    avatar_url = ""
    if tg_info.get("photo_bytes"):
        avatar_url = f"/api/users/{user.telegram_id}/avatar"
    elif init_photo_url:
        avatar_url = init_photo_url
    elif tg_info.get("photo_url"):
        avatar_url = tg_info.get("photo_url")

    # Foydalanuvchi ismini yangilash agar "Foydalanuvchi" bo'lsa
    name_parts = (user.full_name or "").split(" ", 1)
    first_name = name_parts[0] if name_parts and name_parts[0] else (tg_info.get("first_name") or "Foydalanuvchi")
    last_name = name_parts[1] if len(name_parts) > 1 else (tg_info.get("last_name") or "")

    if (not user.full_name or user.full_name == "Foydalanuvchi") and tg_info.get("first_name"):
        first_name = tg_info.get("first_name") or "Foydalanuvchi"
        last_name = tg_info.get("last_name") or ""
        updated_full_name = f"{first_name} {last_name}".strip()
        await conn.execute("UPDATE users SET full_name = ? WHERE id = ?", (updated_full_name, user.id))
        await conn.commit()

    # Determine role
    role = user.role
    if telegram_id in settings.bot.admin_ids or user.role == "admin":
        role = "super_mentor"
    elif user.role == "mentor":
        role = "mentor"
    else:
        cursor = await conn.execute(
            "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1",
            (user.id,),
        )
        if await cursor.fetchone():
            role = "mentor"
        else:
            role = "student"

    # Calculate real student statistics
    grants_cursor = await conn.execute(
        "SELECT COUNT(DISTINCT course_id) as cnt FROM access_grants WHERE user_id = ? AND status = 'active'",
        (user.id,),
    )
    grants_row = await grants_cursor.fetchone()
    enrolled_count = grants_row["cnt"] if grants_row else 0

    views_cursor = await conn.execute(
        """
        SELECT 
            COUNT(CASE WHEN completion_percent >= 90 THEN 1 END) as completed_count,
            COALESCE(SUM(watch_duration_sec), 0) as total_watch_sec
        FROM lesson_views
        WHERE user_id = ?
        """,
        (user.id,),
    )
    views_row = await views_cursor.fetchone()
    completed_lessons = views_row["completed_count"] if views_row else 0
    total_study_minutes = round((views_row["total_watch_sec"] if views_row else 0) / 60)

    streak_cursor = await conn.execute(
        """
        SELECT COUNT(DISTINCT date(started_at)) as streak
        FROM lesson_views
        WHERE user_id = ? AND started_at >= datetime('now', '-7 days')
        """,
        (user.id,),
    )
    streak_row = await streak_cursor.fetchone()
    streak_days = streak_row["streak"] if streak_row else 1

    return {
        "id": f"u-{user.id}",
        "telegram_id": user.telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": clean_username,
        "phone": user.phone or "+998 90 000 00 00",
        "avatar": avatar_url,
        "role": role,
        "is_admin": (telegram_id in settings.bot.admin_ids) or (user.role == "admin"),
        "assigned_mentor_id": "mentor-1",
        "enrolled_courses_count": enrolled_count,
        "completed_lessons_count": completed_lessons,
        "total_study_time_minutes": total_study_minutes,
        "streak_days": max(1, streak_days),
        "joined_date": user.created_at[:10] if user.created_at else "2026",
        "wallet_balance": 0,
        "certificate_count": 1 if completed_lessons >= 10 else 0,
    }


@router.put("/users/profile")
async def update_user_profile(
    updates: UserProfileUpdate,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    full_name = None
    if updates.first_name or updates.last_name:
        parts = []
        if updates.first_name:
            parts.append(updates.first_name)
        if updates.last_name:
            parts.append(updates.last_name)
        full_name = " ".join(parts)

    if full_name or updates.phone:
        await conn.execute(
            """
            UPDATE users 
            SET full_name = COALESCE(?, full_name),
                phone = COALESCE(?, phone)
            WHERE id = ?
            """,
            (full_name, updates.phone, user.id),
        )
        await conn.commit()

    if updates.role and updates.role in ["student", "mentor", "admin"]:
        if telegram_id in settings.bot.admin_ids:
            await user_repo.update_role(user.id, updates.role)

    return await get_user_profile(telegram_id=telegram_id)


@router.get("/mentors")
async def list_mentors() -> list[dict]:
    conn = database.conn
    cursor = await conn.execute(
        """
        SELECT 
            u.id,
            u.telegram_id,
            u.full_name,
            ln.stage,
            ln.royalty_percent
        FROM users u
        JOIN license_nodes ln ON u.id = ln.owner_user_id
        GROUP BY u.id
        """
    )
    rows = await cursor.fetchall()
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


class MentorApplicationCreate(BaseModel):
    full_name: str
    phone: str
    course_direction: str
    experience_bio: str
    telegram_username: str | None = None


class MentorReceiptSubmit(BaseModel):
    application_id: int
    receipt_photo_id: str


@router.post("/users/mentor-application")
@router.post("/mentor-application")
async def create_mentor_application(
    payload: MentorApplicationCreate,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    from db.repositories.mentor_application_repo import MentorApplicationRepository
    app_repo = MentorApplicationRepository(conn)
    app_id = await app_repo.create(
        user_id=user.id,
        full_name=payload.full_name,
        phone=payload.phone,
        course_direction=payload.course_direction,
        experience_bio=payload.experience_bio,
        telegram_username=payload.telegram_username,
    )

    # 🔔 O'zbekcha sana/vaqt formati
    months_map = {
        1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel",
        5: "may", 6: "iyun", 7: "iyul", 8: "avgust",
        9: "sentabr", 10: "oktabr", 11: "noyabr", 12: "dekabr"
    }
    def _format_uzbek_dt(raw_dt: str | None = None) -> str:
        from datetime import datetime
        if not raw_dt:
            now = datetime.now()
            return f"{now.day}-{months_map.get(now.month, '')} {now.year}-yil, {now.strftime('%H:%M')}"
        try:
            clean_str = raw_dt.replace("T", " ")[:19]
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
            return f"{dt.day}-{months_map.get(dt.month, '')} {dt.year}-yil, {dt.strftime('%H:%M')}"
        except Exception:
            return raw_dt[:16] if raw_dt else "Noma'lum"

    # Biriktirilgan mentor va kabinetni aniqlash
    cursor = await conn.execute(
        """
        SELECT 
            cab.display_name as cabinet_name,
            mentor_user.full_name as mentor_name,
            mentor_user.telegram_id as mentor_tg_id
        FROM cabinet_members cm
        JOIN cabinets cab ON cab.id = cm.cabinet_id
        JOIN license_nodes ln ON ln.id = cab.owner_node_id
        JOIN users mentor_user ON mentor_user.id = ln.owner_user_id
        WHERE cm.user_id = ?
        LIMIT 1
        """,
        (user.id,),
    )
    mentor_row = await cursor.fetchone()
    if mentor_row:
        mentor_display = f"{mentor_row['mentor_name']} (ID: <code>{mentor_row['mentor_tg_id']}</code>)"
        cabinet_display = mentor_row["cabinet_name"]
    else:
        mentor_display = "To'g'ridan-to'g'ri (Platforma)"
        cabinet_display = "Hali biriktirilmagan"

    # O'qiyotgan faol kursni aniqlash
    c_cursor = await conn.execute(
        """
        SELECT c.title
        FROM access_grants ag
        JOIN courses c ON c.id = ag.course_id
        WHERE ag.user_id = ? AND ag.status = 'active'
        ORDER BY ag.id DESC
        LIMIT 1
        """,
        (user.id,),
    )
    course_row = await c_cursor.fetchone()
    enrolled_course_display = course_row["title"] if course_row else "Hozircha kurs yo'q"

    registered_time_display = _format_uzbek_dt(user.created_at)
    submission_time_display = _format_uzbek_dt()

    # 🔔 Adminga / guruhga boyitilgan xabarnoma matni
    tg_user_link = f"@{payload.telegram_username.lstrip('@')}" if payload.telegram_username else f"ID: {user.telegram_id}"
    admin_notify_text = (
        f"👨‍🏫 <b>YANGI MENTORLIK ARIZASI!</b>\n\n"
        f"🆔 <b>Ariza raqami:</b> #{app_id}\n"
        f"👤 <b>F.I.SH:</b> <b>{payload.full_name}</b>\n"
        f"📱 <b>Telefon:</b> <code>{payload.phone}</code>\n"
        f"💬 <b>Telegram:</b> {tg_user_link} (<code>{user.telegram_id}</code>)\n\n"
        f"🎯 <b>Ariza yo'nalishi:</b> {payload.course_direction}\n"
        f"📝 <b>Tajriba / Ma'lumot:</b>\n<i>{payload.experience_bio}</i>\n\n"
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

    async def _send_admin_alerts():
        bot_token = settings.bot.token
        if not bot_token:
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            # SuperMentor guruhidagi '🎓Mentorlik arizalari' mavzusiga (Topic 2) xabarnoma
            group_id = int(os.getenv("SUPER_MENTOR_GROUP_ID", "-1004369887420"))
            topic_id = int(os.getenv("MENTOR_APPLICATIONS_TOPIC_ID", "2"))
            if group_id:
                try:
                    payload_data = {
                        "chat_id": group_id,
                        "text": admin_notify_text,
                        "parse_mode": "HTML",
                    }
                    if topic_id:
                        payload_data["message_thread_id"] = topic_id
                    payload_data["reply_markup"] = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Tasdiqlash", "callback_data": f"mentor_app:approve:{app_id}"},
                                {"text": "❌ Rad etish", "callback_data": f"mentor_app:reject:{app_id}"},
                            ]
                        ]
                    }
                    res = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=payload_data,
                    )
                    logger.info("Mentorlik arizasi guruhga (%s topic %s) yuborildi: %s", group_id, topic_id, res.status_code)
                except Exception as ex:
                    logger.warning("Guruhga xabar yuborishda xatolik: %s", ex)

    import asyncio
    asyncio.create_task(_send_admin_alerts())

    return {
        "success": True,
        "message": "Arizangiz muvaffaqiyatli qabul qilindi!",
        "application_id": app_id,
    }


@router.get("/users/mentor-application/my")
@router.get("/mentor-application/my")
async def get_my_mentor_application(
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    from db.repositories.mentor_application_repo import MentorApplicationRepository
    app_repo = MentorApplicationRepository(conn)
    app = await app_repo.get_latest_by_user_id(user.id)
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


@router.post("/users/mentor-application/receipt")
@router.post("/mentor-application/receipt")
async def submit_mentor_application_receipt(
    payload: MentorReceiptSubmit,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    from db.repositories.mentor_application_repo import MentorApplicationRepository
    app_repo = MentorApplicationRepository(conn)
    app = await app_repo.get_by_id(payload.application_id)
    if not app or app.user_id != user.id:
        raise HTTPException(status_code=404, detail="Ariza topilmadi")

    await conn.execute(
        """
        UPDATE mentor_applications
        SET receipt_photo_id = ?, status = 'receipt_submitted'
        WHERE id = ?
        """,
        (payload.receipt_photo_id, payload.application_id),
    )
    await conn.commit()

    # 🧾 Adminga chek xabarnomasini yuborish
    receipt_notify_text = (
        f"🧾 <b>MENTORLIK TO'LOV CHEKI YUBORILDI!</b>\n\n"
        f"🆔 <b>Ariza raqami:</b> #{payload.application_id}\n"
        f"👤 <b>Nomzod:</b> <b>{app.full_name}</b>\n"
        f"📱 <b>Telefon:</b> <code>{app.phone}</code>\n"
        f"💬 <b>Telegram:</b> {app.telegram_username or f'ID: {user.telegram_id}'}\n"
        f"💰 <b>To'lov summasi:</b> {app.payment_amount:,} so'm\n"
        f"🖼 <b>Chek fayl ID:</b> <code>{payload.receipt_photo_id}</code>\n\n"
        f"⚡️ <i>Iltimos, to'lovni tekshirib arizani tasdiqlang.</i>"
    )

    async def _send_receipt_alerts():
        bot_token = settings.bot.token
        if not bot_token:
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            # SuperMentor guruhidagi '💳To‘lovlar va cheklar' mavzusiga (Topic 4) xabarnoma
            group_id = int(os.getenv("SUPER_MENTOR_GROUP_ID", "-1004369887420"))
            topic_id = int(os.getenv("PAYMENT_RECEIPTS_TOPIC_ID", "4"))
            if group_id:
                try:
                    payload_data = {
                        "chat_id": group_id,
                        "text": receipt_notify_text,
                        "parse_mode": "HTML",
                    }
                    if topic_id:
                        payload_data["message_thread_id"] = topic_id
                    payload_data["reply_markup"] = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Chekni tasdiqlash", "callback_data": f"mentor_receipt:approve:{payload.application_id}"},
                                {"text": "❌ Rad etish", "callback_data": f"mentor_receipt:reject:{payload.application_id}"},
                            ]
                        ]
                    }
                    res = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=payload_data,
                    )
                    logger.info("To'lov cheki guruhga (%s topic %s) yuborildi: %s", group_id, topic_id, res.status_code)
                except Exception as ex:
                    logger.warning("Guruhga chek xabarnomasini yuborishda xatolik: %s", ex)

    import asyncio
    asyncio.create_task(_send_receipt_alerts())

    return {
        "success": True,
        "message": "Chek muvaffaqiyatli yuborildi!",
    }
