from __future__ import annotations

from core.exceptions import AccessDeniedError, NotFoundError
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.live_session_repo import LiveSession, LiveSessionRepository


class LiveSessionService:
    def __init__(
        self, live_repo: LiveSessionRepository, access_grant_repo: AccessGrantRepository
    ) -> None:
        self._live_repo = live_repo
        self._access_grant_repo = access_grant_repo

    async def schedule(
        self, course_id: int, mentor_id: int, scheduled_at: str, join_method: str = "webapp"
    ) -> int:
        return await self._live_repo.create(course_id, mentor_id, scheduled_at, join_method)

    async def start(self, session_id: int, stream_ref: str) -> None:
        await self._live_repo.set_status(session_id, "live", stream_ref)

    async def end(self, session_id: int) -> None:
        await self._live_repo.set_status(session_id, "ended")

    async def join(self, session_id: int, user_id: int) -> LiveSession:
        session = await self._live_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(f"Live session topilmadi: id={session_id}")
        if session.status != "live":
            raise AccessDeniedError("Live dars hozircha faol emas")

        has_access = await self._access_grant_repo.has_active_access(
            user_id=user_id, lesson_id=-1, course_id=session.course_id
        )
        if not has_access:
            raise AccessDeniedError("Ushbu kursga kirish huquqi yo'q")

        await self._live_repo.record_join(session_id, user_id)
        return session

    async def leave(self, session_id: int, user_id: int) -> None:
        await self._live_repo.record_leave(session_id, user_id)
