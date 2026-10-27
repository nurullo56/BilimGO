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

    async def try_claim_course_notification(self, user_id: int, course_id: int, notification_type: str) -> bool:
        """Atomik ravishda xabar yuborish huquqini bron qiladi.
        Agar boshqa parallel jarayon allaqachon bron qilgan yoki yuborgan bo'lsa False qaytaradi."""
        cursor = await self._conn.execute(
            """
            INSERT INTO course_notifications (user_id, course_id, notification_type, status)
            VALUES (?, ?, ?, 'sending')
            ON CONFLICT(user_id, course_id, notification_type) DO NOTHING
            """,
            (user_id, course_id, notification_type),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def mark_course_notified(
        self, user_id: int, course_id: int, notification_type: str, status: str = "sent"
    ) -> None:
        await self._conn.execute(
            """
            UPDATE course_notifications
            SET status = ?, notified_at = datetime('now')
            WHERE user_id = ? AND course_id = ? AND notification_type = ?
            """,
            (status, user_id, course_id, notification_type),
        )
        await self._conn.commit()

    async def is_course_notified(self, user_id: int, course_id: int, notification_type: str) -> bool:
        cursor = await self._conn.execute(
            """
            SELECT 1 FROM course_notifications
            WHERE user_id = ? AND course_id = ? AND notification_type = ? AND status = 'sent'
            """,
            (user_id, course_id, notification_type),
        )
        return await cursor.fetchone() is not None
