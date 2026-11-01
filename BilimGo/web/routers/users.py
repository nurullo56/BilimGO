from __future__ import annotations

import logging
import time
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
import httpx
from pydantic import BaseModel

from core.config import settings
from db.database import database
from services.user_service import UserService
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["users"])


class UserProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str | None = None


class MentorApplicationCreate(BaseModel):
    full_name: str
    phone: str
    course_direction: str
    experience_bio: str
    telegram_username: str | None = None


class MentorReceiptSubmit(BaseModel):
    application_id: int
    receipt_photo_id: str


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
                            r_img = await client.get(photo_url)
                            if r_img.is_success:
                                info["photo_bytes"] = r_img.content
    except Exception as exc:
        logger.warning(f"Telegram user info fetch error for {telegram_id}: {exc}")

    _USER_CACHE[telegram_id] = info
    return info


def _get_user_service() -> UserService:
    return UserService.create_default(database.conn)


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
    service: UserService = Depends(_get_user_service),
) -> dict:
    tg_info = await _fetch_telegram_user_info(telegram_id)
    return await service.get_full_profile(
        telegram_id=telegram_id,
        x_telegram_init_data=x_telegram_init_data,
        tg_info=tg_info,
        admin_ids=settings.bot.admin_ids,
    )


@router.put("/users/profile")
async def update_user_profile(
    updates: UserProfileUpdate,
    telegram_id: int = Depends(get_current_telegram_id),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    service: UserService = Depends(_get_user_service),
) -> dict:
    await service.update_profile_info(
        telegram_id=telegram_id,
        first_name=updates.first_name,
        last_name=updates.last_name,
        phone=updates.phone,
        role=updates.role,
        admin_ids=settings.bot.admin_ids,
    )
    tg_info = await _fetch_telegram_user_info(telegram_id)
    return await service.get_full_profile(
        telegram_id=telegram_id,
        x_telegram_init_data=x_telegram_init_data,
        tg_info=tg_info,
        admin_ids=settings.bot.admin_ids,
    )


@router.get("/mentors")
async def list_mentors(
    service: UserService = Depends(_get_user_service),
) -> list[dict]:
    return await service.list_mentors_directory()


@router.post("/users/mentor-application")
@router.post("/mentor-application")
async def create_mentor_application(
    payload: MentorApplicationCreate,
    telegram_id: int = Depends(get_current_telegram_id),
    service: UserService = Depends(_get_user_service),
) -> dict:
    return await service.create_mentor_application(
        telegram_id=telegram_id,
        full_name=payload.full_name,
        phone=payload.phone,
        course_direction=payload.course_direction,
        experience_bio=payload.experience_bio,
        telegram_username=payload.telegram_username,
    )


@router.get("/users/mentor-application/my")
@router.get("/mentor-application/my")
async def get_my_mentor_application(
    telegram_id: int = Depends(get_current_telegram_id),
    service: UserService = Depends(_get_user_service),
) -> dict:
    return await service.get_my_mentor_application(telegram_id)


@router.post("/users/mentor-application/receipt")
@router.post("/mentor-application/receipt")
async def submit_mentor_application_receipt(
    payload: MentorReceiptSubmit,
    telegram_id: int = Depends(get_current_telegram_id),
    service: UserService = Depends(_get_user_service),
) -> dict:
    try:
        return await service.submit_mentor_application_receipt(
            telegram_id=telegram_id,
            application_id=payload.application_id,
            receipt_photo_id=payload.receipt_photo_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
