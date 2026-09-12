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
