from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import settings
from core.exceptions import AccessDeniedError, NotFoundError
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.live_session_repo import LiveSession, LiveSessionRepository
from services.live_stream_service import live_manager

logger = logging.getLogger(__name__)


class LiveSessionService:
    """Live sessiyalar bo'yicha yagona xizmat qatlami (Service Layer)."""

    def __init__(
        self, live_repo: LiveSessionRepository, access_grant_repo: AccessGrantRepository
    ) -> None:
        self._live_repo = live_repo
        self._access_grant_repo = access_grant_repo

    @classmethod
    def create_default(cls, conn=None) -> "LiveSessionService":
        from db.database import database
        from db.repositories.access_grant_repo import AccessGrantRepository
        from db.repositories.live_session_repo import LiveSessionRepository

        c = conn or database.conn
        return cls(
            live_repo=LiveSessionRepository(c),
            access_grant_repo=AccessGrantRepository(c),
        )

    async def schedule(
        self,
        course_id: int,
        mentor_id: int,
        scheduled_at: str | datetime,
        title: Optional[str] = None,
        description: Optional[str] = None,
        join_method: str = "webapp",
    ) -> Dict[str, Any]:
        """Yangi jonli efir sessiyasini rejalashtirish."""
        sched_dt = scheduled_at if isinstance(scheduled_at, datetime) else None
        return await live_manager.create_session(
            course_id=course_id,
            mentor_id=mentor_id,
            title=title or "Jonli dars",
            description=description or "",
            scheduled_at=sched_dt,
        )

    async def list_upcoming(self, course_id: int | str) -> List[Dict[str, Any]]:
        """Kurs bo'yicha faol yoki rejalashtirilgan sessiyalar ro'yxatini olish."""
        try:
            clean_course_id = int(str(course_id).replace("course-", ""))
        except ValueError:
            clean_course_id = 1

        # 3 soatdan oshib ketgan rejalashtirilgan sessiyalarni avtomatik tugatish
        await self._live_repo.expire_old_scheduled_sessions(cutoff_hours=3)

        rows = await self._live_repo.list_upcoming_with_details(clean_course_id)

        return [
            {
                "id": r["id"],
                "course_id": r["course_id"],
                "title": r["title"] or f"{r['course_title'] or 'Kurs'}: Jonli efir",
                "scheduled_at": r["scheduled_at"],
                "status": r["status"],
                "join_method": r["join_method"] or "webapp",
                "stream_ref": r["stream_ref"] or f"/live/{r['id']}",
                "instructor_name": r["instructor_name"] or "Nurulloh Habibullayev",
                "viewer_count": r["viewer_count"] or 0,
            }
            for r in rows
        ]

    async def get_session(self, session_id: int | str) -> Optional[Dict[str, Any]]:
        """Sessiya ma'lumotlarini olish."""
        clean_id = str(session_id).replace("live_", "").replace("live-", "")
        return await live_manager.get_session_info(clean_id)

    async def start(self, session_id: int | str, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Sessiyani 'live' holatiga o'tkazish."""
        clean_id = str(session_id).replace("live_", "").replace("live-", "")
        return await live_manager.start_session(clean_id, stream_key)

    async def end(self, session_id: int | str) -> Dict[str, Any]:
        """Sessiyani tugatish ('ended')."""
        clean_id = str(session_id).replace("live_", "").replace("live-", "")
        return await live_manager.end_session(clean_id)

    async def join(self, session_id: int | str, user_id: int) -> Dict[str, Any]:
        """Talaba sessiyaga qo'shilganda ruxsatni tekshirish va qatnashuvni qayd etish."""
        clean_id = str(session_id).replace("live_", "").replace("live-", "")
        session_info = await live_manager.get_session_info(clean_id)
        if not session_info:
            session_db = await self._live_repo.get_by_id(clean_id)
            if not session_db:
                raise NotFoundError(f"Live session topilmadi: id={session_id}")
            course_id = session_db.course_id
            session_status = session_db.status
        else:
            course_id = session_info.get("course_id", 1)
            session_status = session_info.get("status", "live")

        if session_status not in ("live", "scheduled"):
            raise AccessDeniedError("Ushbu dars hozirda faol emas yoki yakunlangan")

        # Kursga ruxsatni tekshirish
        has_access = await self._access_grant_repo.has_active_access(
            user_id=user_id, lesson_id=-1, course_id=course_id
        )
        if not has_access:
            # Agar mentor yoki admin bo'lsa kirishga ruxsat
            role = await self._live_repo.get_user_role(user_id)
            if role not in ("admin", "mentor", "super_mentor"):
                raise AccessDeniedError("Ushbu kursga kirish huquqi yo'q")

        await self._live_repo.record_join(clean_id, user_id)
        return {
            "session_id": clean_id,
            "stream_ref": f"/live/{clean_id}",
            "join_method": "webapp",
            "status": session_status,
        }

    async def leave(self, session_id: int | str, user_id: int) -> None:
        """Sessiyadan chiqishni qayd etish."""
        clean_id = str(session_id).replace("live_", "").replace("live-", "")
        await self._live_repo.record_leave(clean_id, user_id)

    async def get_session_audience_students(
        self, session_id: int | str, mentor_id: int
    ) -> List[Dict[str, Any]]:
        """
        Jonli efir bildirishnomasi yuboriladigan talabalar ro'yxatini olish.
        Maxfiylik va xavfsizlik kafolatlangan:
        - Agar Super Admin bo'lsa (admin_ids yoki mentor_id == 1): Ushbu kursdagi barcha faol talabalarga yuboriladi.
        - Agar quyi mentor bo'lsa: FAQAT shu mentorning o'ziga biriktirilgan (litsenziya tuguni yoki kabineti a'zosi bo'lgan) talabalarga yuboriladi.
        Hech qachon boshqa begona mentorlar yoki butun platforma talabalariga xabar ketmaydi.
        """
        clean_id = str(session_id).replace("live_", "").replace("live-", "")
        session_info = await live_manager.get_session_info(clean_id)
        if session_info:
            course_id = session_info.get("course_id", 1)
        else:
            session_db = await self._live_repo.get_by_id(clean_id)
            course_id = session_db.course_id if session_db else 1

        admin_ids = getattr(settings.bot, "admin_ids", []) or []
        is_admin = mentor_id in admin_ids or mentor_id == 1

        if is_admin:
            return await self._live_repo.get_course_active_students_audience(course_id)

        # Quyi mentor: faqat ushbu mentorga tegishli shogirdlar (litsenziya va kabinet bo'yicha)
        return await self._live_repo.get_mentor_course_audience_students(mentor_id, course_id)
