from __future__ import annotations

import logging
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
