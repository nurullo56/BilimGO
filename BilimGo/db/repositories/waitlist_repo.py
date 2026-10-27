from __future__ import annotations

from typing import Any
from db.repositories.base import BaseRepository


class WaitlistRepository(BaseRepository):
    async def join_waitlist(
        self, course_id: int, user_id: int, phone: str | None = None
    ) -> bool:
        cursor = await self._conn.execute(
            """
            INSERT INTO course_waitlist (course_id, user_id, phone)
            VALUES (?, ?, ?)
            ON CONFLICT(course_id, user_id) DO UPDATE SET
                created_at = datetime('now')
            """,
            (course_id, user_id, phone),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def leave_waitlist(self, course_id: int, user_id: int) -> bool:
        cursor = await self._conn.execute(
            "DELETE FROM course_waitlist WHERE course_id = ? AND user_id = ?",
            (course_id, user_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def is_in_waitlist(self, course_id: int, user_id: int) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM course_waitlist WHERE course_id = ? AND user_id = ?",
            (course_id, user_id),
        )
        row = await cursor.fetchone()
        return row is not None

    async def get_count(self, course_id: int) -> int:
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM course_waitlist WHERE course_id = ?",
            (course_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_waitlist_users(self, course_id: int) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(
            """
            SELECT u.id, u.telegram_id, u.full_name, u.phone, cw.created_at
            FROM course_waitlist cw
            JOIN users u ON u.id = cw.user_id
            WHERE cw.course_id = ?
            ORDER BY cw.created_at ASC
            """,
            (course_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
