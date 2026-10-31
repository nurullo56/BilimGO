from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from core.exceptions import AccessDeniedError, NotFoundError
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.live_session_repo import LiveSessionRepository
from db.repositories.user_repo import UserRepository
from services.live_session_service import LiveSessionService
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live", tags=["live"])


def _build_service() -> LiveSessionService:
    conn = database.conn
    return LiveSessionService(LiveSessionRepository(conn), AccessGrantRepository(conn))


@router.get("/courses/{course_id}/sessions")
async def list_upcoming(course_id: int | str) -> List[Dict[str, Any]]:
    """Kursga tegishli faol va rejalashtirilgan barcha Live sessiyalarni olish."""
    service = _build_service()
    return await service.list_upcoming(course_id)


@router.get("/sessions/{session_id}")
async def get_session(session_id: int | str) -> Dict[str, Any]:
    """Muayyan Live sessiya ma'lumotlarini olish."""
    service = _build_service()
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Live sessiya topilmadi")
    return session


@router.post("/sessions/{session_id}/join")
async def join_session(
    session_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> Dict[str, Any]:
    """Live sessiyaga qo'shilish va kirish huquqini tekshirish."""
    clean_session_id = int(str(session_id).replace("live-", "").replace("live_", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    service = _build_service()
    try:
        return await service.join(clean_session_id, user.id)
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as exc:
        logger.exception("Live sessiyaga qo'shilishda xatolik: %s", exc)
        return {
            "session_id": str(clean_session_id),
            "stream_ref": f"/live/{clean_session_id}",
            "join_method": "webapp",
            "status": "live",
        }


@router.post("/sessions/{session_id}/leave")
async def leave_session(
    session_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> Dict[str, str]:
    """Live sessiyadan chiqishni qayd etish."""
    clean_session_id = int(str(session_id).replace("live-", "").replace("live_", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    try:
        await _build_service().leave(clean_session_id, user.id)
    except Exception as exc:
        logger.debug("Live sessiyadan chiqishda xatolik: %s", exc)
    return {"status": "left"}


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> Dict[str, Any]:
    """Mentor jonli efirni boshlaganda 'live' holatiga o'tkazish."""
    clean_session_id = int(str(session_id).replace("live-", "").replace("live_", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    if user.role not in ("admin", "super_mentor", "mentor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat mentor efirni boshlashi mumkin")
    service = _build_service()
    return await service.start(clean_session_id)


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> Dict[str, Any]:
    """Mentor jonli efirni tugatganda 'ended' holatiga o'tkazish."""
    clean_session_id = int(str(session_id).replace("live-", "").replace("live_", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    if user.role not in ("admin", "super_mentor", "mentor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat mentor efirni tugatishi mumkin")
    service = _build_service()
    return await service.end(clean_session_id)
