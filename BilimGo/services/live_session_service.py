from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

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
        conn = self._live_repo._conn
        try:
            clean_course_id = int(str(course_id).replace("course-", ""))
        except ValueError:
            clean_course_id = 1

        # 3 soatdan oshib ketgan rejalashtirilgan sessiyalarni avtomatik tugatish
        await conn.execute(
            """
            UPDATE live_sessions
            SET status = 'ended', ended_at = datetime('now')
            WHERE status = 'scheduled'
              AND datetime(scheduled_at) < datetime('now', '-3 hours')
            """
        )
        await conn.commit()

        cursor = await conn.execute(
            """
            SELECT ls.id, ls.course_id, ls.scheduled_at, ls.status, ls.join_method, ls.stream_ref,
                   ls.title, ls.viewer_count,
                   u.full_name AS instructor_name, c.title AS course_title
            FROM live_sessions ls
            LEFT JOIN users u ON u.id = ls.mentor_id
            LEFT JOIN courses c ON c.id = ls.course_id
            WHERE ls.course_id = ?
            ORDER BY 
                CASE 
                    WHEN ls.status = 'live' THEN 1
                    WHEN ls.status = 'scheduled' THEN 2
                    ELSE 3
                END,
                ls.scheduled_at DESC
            """,
            (clean_course_id,),
        )
        rows = await cursor.fetchall()

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
            user_row = await self._live_repo._conn.execute(
                "SELECT role FROM users WHERE id = ?", (user_id,)
            )
            u = await user_row.fetchone()
            if not u or u["role"] not in ("admin", "mentor", "super_mentor"):
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
