from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.config import settings
from core.exceptions import AccessDeniedError
from db.repositories.delivery_token_repo import DeliveryTokenRepository
from db.repositories.lesson_repo import Lesson, LessonRepository
from services.access_control_service import AccessControlService


@dataclass(slots=True)
class IssuedToken:
    raw_token: str
    expires_at: str


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class DeliveryTokenService:
    def __init__(
        self,
        access_control: AccessControlService,
        token_repo: DeliveryTokenRepository,
        lesson_repo: LessonRepository,
    ) -> None:
        self._access_control = access_control
        self._token_repo = token_repo
        self._lesson_repo = lesson_repo

    async def issue(self, user_id: int, lesson_id: int) -> IssuedToken:
        await self._access_control.ensure_can_watch(user_id, lesson_id)

        raw_token = secrets.token_urlsafe(32)
        expires_at = (
            datetime.utcnow() + timedelta(seconds=settings.delivery.token_ttl_seconds)
        ).isoformat(timespec="seconds")

        await self._token_repo.create(
            user_id=user_id,
            lesson_id=lesson_id,
            token_hash=_hash_token(raw_token),
            expires_at=expires_at,
        )
        return IssuedToken(raw_token=raw_token, expires_at=expires_at)

    async def resolve(self, raw_token: str) -> Lesson:
        """Token orqali darsni topadi. Amal qilish muddati va mavjudligini
        tekshiradi, keyin manba ma'lumotlarini (source_channel_id/message_id)
        qaytaradi — bu ma'lumot brauzerga hech qachon uzatilmaydi."""
        token_hash = _hash_token(raw_token)
        token = await self._token_repo.get_by_hash(token_hash)

        if token is None or not token.is_valid():
            raise AccessDeniedError("Token yaroqsiz yoki muddati o'tgan")

        if token.used_at is None:
            await self._token_repo.mark_activated(token_hash)

        lesson = await self._lesson_repo.get_by_id(token.lesson_id)
        if lesson is None:
            raise AccessDeniedError("Token bog'langan dars topilmadi")
        return lesson
