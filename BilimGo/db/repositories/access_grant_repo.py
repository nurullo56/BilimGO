from __future__ import annotations

from db.repositories.base import BaseRepository


class AccessGrantRepository(BaseRepository):
    async def grant_course_access(
        self, user_id: int, course_id: int, granted_via_sale_id: int
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO access_grants (user_id, course_id, granted_via_sale_id, status)
            VALUES (?, ?, ?, 'active')
            """,
            (user_id, course_id, granted_via_sale_id),
        )
        await self._conn.commit()

    async def has_active_access(self, user_id: int, lesson_id: int, course_id: int) -> bool:
        cursor = await self._conn.execute(
            """
            SELECT 1 FROM access_grants
            WHERE user_id = ?
              AND status = 'active'
              AND (
                  course_id = ?
                  OR (lesson_id IS NOT NULL AND lesson_id = ?)
              )
              AND (expires_at IS NULL OR expires_at > datetime('now'))
            LIMIT 1
            """,
            (user_id, course_id, lesson_id),
        )
        row = await cursor.fetchone()
        return row is not None
