from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class LiveSession:
    id: int
    course_id: int
    mentor_id: int
    scheduled_at: str
    status: str
    join_method: str
    stream_ref: str | None
    title: str | None = None
    description: str | None = None
    stream_key: str | None = None
    viewer_count: int = 0
    total_viewers: int = 0
    started_at: str | None = None
    ended_at: str | None = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> LiveSession:
        return cls(
            id=row["id"],
            course_id=row["course_id"],
            mentor_id=row["mentor_id"],
            scheduled_at=row["scheduled_at"],
            status=row["status"],
            join_method=row["join_method"] if "join_method" in row.keys() else "webapp",
            stream_ref=row["stream_ref"] if "stream_ref" in row.keys() else None,
            title=row["title"] if "title" in row.keys() else None,
            description=row["description"] if "description" in row.keys() else None,
            stream_key=row["stream_key"] if "stream_key" in row.keys() else None,
            viewer_count=row["viewer_count"] if "viewer_count" in row.keys() else 0,
            total_viewers=row["total_viewers"] if "total_viewers" in row.keys() else 0,
            started_at=row["started_at"] if "started_at" in row.keys() else None,
            ended_at=row["ended_at"] if "ended_at" in row.keys() else None,
        )


class LiveSessionRepository(BaseRepository):
    async def create(
        self,
        course_id: int,
        mentor_id: int,
        scheduled_at: str | None = None,
        join_method: str = "webapp",
        title: str | None = None,
        description: str | None = None,
        stream_ref: str | None = None,
    ) -> int:
        scheduled_str = scheduled_at or ""
        cursor = await self._conn.execute(
            """
            INSERT INTO live_sessions (course_id, mentor_id, scheduled_at, join_method, title, description, stream_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (course_id, mentor_id, scheduled_str, join_method, title, description, stream_ref),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_by_id(self, session_id: int | str) -> LiveSession | None:
        numeric_id = int(str(session_id).replace("live_", "")) if str(session_id).replace("live_", "").isdigit() else session_id
        cursor = await self._conn.execute(
            "SELECT * FROM live_sessions WHERE id = ?", (numeric_id,)
        )
        row = await cursor.fetchone()
        return LiveSession.from_row(row) if row else None

    async def list_upcoming(self, course_id: int) -> list[LiveSession]:
        cursor = await self._conn.execute(
            """
            SELECT * FROM live_sessions
            WHERE course_id = ? AND status IN ('scheduled', 'live')
            ORDER BY scheduled_at
            """,
            (course_id,),
        )
        rows = await cursor.fetchall()
        return [LiveSession.from_row(r) for r in rows]

    async def set_status(self, session_id: int | str, status: str, stream_key: str | None = None) -> None:
        numeric_id = int(str(session_id).replace("live_", "")) if str(session_id).replace("live_", "").isdigit() else session_id
        if stream_key is not None:
            await self._conn.execute(
                "UPDATE live_sessions SET status = ?, stream_key = ?, started_at = datetime('now') WHERE id = ?",
                (status, stream_key, numeric_id),
            )
        elif status == "ended":
            await self._conn.execute(
                "UPDATE live_sessions SET status = ?, ended_at = datetime('now') WHERE id = ?",
                (status, numeric_id),
            )
        else:
            await self._conn.execute(
                "UPDATE live_sessions SET status = ? WHERE id = ?", (status, numeric_id)
            )
        await self._conn.commit()

    async def record_join(self, session_id: int | str, user_id: int) -> None:
        numeric_id = int(str(session_id).replace("live_", "")) if str(session_id).replace("live_", "").isdigit() else session_id
        await self._conn.execute(
            """
            INSERT INTO live_attendance (session_id, user_id)
            VALUES (?, ?)
            ON CONFLICT(session_id, user_id) DO NOTHING
            """,
            (numeric_id, user_id),
        )
        await self._conn.commit()

    async def record_leave(self, session_id: int | str, user_id: int) -> None:
        numeric_id = int(str(session_id).replace("live_", "")) if str(session_id).replace("live_", "").isdigit() else session_id
        await self._conn.execute(
            """
            UPDATE live_attendance SET left_at = datetime('now')
            WHERE session_id = ? AND user_id = ?
            """,
            (numeric_id, user_id),
        )
        await self._conn.commit()

    async def expire_old_scheduled_sessions(self, cutoff_hours: int = 3) -> None:
        """3 soatdan oshib ketgan rejalashtirilgan sessiyalarni avtomatik tugatish."""
        modifier = f"-{cutoff_hours} hours"
        await self._conn.execute(
            """
            UPDATE live_sessions
            SET status = 'ended', ended_at = datetime('now')
            WHERE status = 'scheduled'
              AND datetime(scheduled_at) < datetime('now', ?)
            """,
            (modifier,),
        )
        await self._conn.commit()

    async def list_upcoming_with_details(self, course_id: int) -> list[dict[str, Any]]:
        """Kurs bo'yicha sessiyalar va ularning mentor/kurs ma'lumotlarini olish."""
        cursor = await self._conn.execute(
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
            (course_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_role(self, user_id: int) -> str | None:
        """Foydalanuvchi rolini olish."""
        cursor = await self._conn.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row["role"] if row else None

    async def get_course_active_students_audience(self, course_id: int) -> list[dict[str, Any]]:
        """Kursdagi barcha faol talabalar (super admin jonli efiri uchun)."""
        cursor = await self._conn.execute(
            """
            SELECT DISTINCT u.telegram_id, u.full_name
            FROM access_grants ag
            JOIN users u ON u.id = ag.user_id
            WHERE ag.course_id = ? AND ag.status = 'active'
              AND u.telegram_id IS NOT NULL
            """,
            (course_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_mentor_course_audience_students(self, mentor_id: int, course_id: int) -> list[dict[str, Any]]:
        """Quyi mentorga biriktirilgan shogirdlar (litsenziya va kabinet bo'yicha)."""
        cursor = await self._conn.execute(
            """
            SELECT DISTINCT u.telegram_id, u.full_name
            FROM users u
            WHERE u.telegram_id IS NOT NULL 
              AND u.status = 'active'
              AND (
                  u.id IN (
                      SELECT ag.user_id 
                      FROM access_grants ag
                      JOIN sales s ON s.id = ag.granted_via_sale_id
                      JOIN license_nodes ln ON ln.id = s.license_node_id
                      WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                  )
                  OR u.id IN (
                      SELECT cm.user_id 
                      FROM cabinet_members cm
                      JOIN cabinets c ON c.id = cm.cabinet_id
                      JOIN license_nodes ln ON ln.id = c.owner_node_id
                      WHERE ln.owner_user_id = ? AND cm.role_in_cabinet = 'student'
                  )
              )
            """,
            (mentor_id, course_id, mentor_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
