from __future__ import annotations

from db.repositories.base import BaseRepository


class CompletionNotificationRepository(BaseRepository):
    async def is_notified(self, user_id: int, lesson_id: int) -> bool:
        cursor = await self._conn.execute(
            """
            SELECT 1 FROM completion_notifications
            WHERE user_id = ? AND lesson_id = ? AND status = 'sent'
            """,
            (user_id, lesson_id),
        )
        return await cursor.fetchone() is not None

    async def mark_notified(self, user_id: int, lesson_id: int, status: str = "sent") -> None:
        await self._conn.execute(
            """
            INSERT INTO completion_notifications (user_id, lesson_id, status)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, lesson_id) DO UPDATE SET
                status = excluded.status,
                notified_at = datetime('now')
            """,
            (user_id, lesson_id, status),
        )
        await self._conn.commit()
