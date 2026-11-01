from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from db.database import database
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.user_repo import UserRepository
from services.cabinet_service import CabinetService
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cabinets", tags=["cabinets"])


class CreateCabinetPayload(BaseModel):
    display_name: str
    avatar: str | None = "💬"
    description: str | None = None
    course_id: int | str | None = None
    course_title: str | None = None
    initial_message: str | None = None


def _get_cabinet_service() -> CabinetService:
    return CabinetService.create_default(database.conn)


@router.get("/me")
async def my_cabinets(
    telegram_id: int = Depends(get_current_telegram_id),
    service: CabinetService = Depends(_get_cabinet_service),
) -> list[dict]:
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    is_admin = user.role in ("admin", "super_mentor")
    return await service.get_user_cabinets(user.id, is_admin)


@router.get("/{cabinet_id}/students")
async def cabinet_students(
    cabinet_id: str | int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict]:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    return await CabinetRepository(database.conn).list_students(clean_id)


@router.get("/{cabinet_id}/rooms")
async def cabinet_rooms(
    cabinet_id: str | int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict]:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    return await ChatRepository(database.conn).list_rooms_for_cabinet(clean_id)


@router.post("")
async def create_cabinet(
    payload: CreateCabinetPayload,
    telegram_id: int = Depends(get_current_telegram_id),
    service: CabinetService = Depends(_get_cabinet_service),
) -> dict:
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    return await service.create_cabinet_flow(
        creator_user_id=user.id,
        display_name=payload.display_name,
        avatar=payload.avatar,
        description=payload.description,
        course_id=payload.course_id,
        course_title=payload.course_title,
        initial_message=payload.initial_message,
    )


@router.put("/{cabinet_id}")
async def update_cabinet(
    cabinet_id: str | int,
    payload: CreateCabinetPayload,
    telegram_id: int = Depends(get_current_telegram_id),
    service: CabinetService = Depends(_get_cabinet_service),
) -> dict:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    return await service.update_cabinet_branding(
        cabinet_id=clean_id,
        display_name=payload.display_name,
        avatar=payload.avatar,
        description=payload.description,
        course_title=payload.course_title,
    )


@router.delete("/{cabinet_id}")
async def delete_cabinet(
    cabinet_id: str | int,
    telegram_id: int = Depends(get_current_telegram_id),
    service: CabinetService = Depends(_get_cabinet_service),
) -> dict:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    await service.delete_cabinet(clean_id)
    return {"success": True}
