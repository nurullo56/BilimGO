from __future__ import annotations

from typing import Any
from db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    async def create_notification(
        self,
        user_id: int,
        type: str,
        title: str,
        message: str,
        link: str | None = None,
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO user_notifications (user_id, type, title, message, link, is_read)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (user_id, type, title, message, link),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_user_notifications(self, user_id: int, limit: int = 40) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(
            """
            SELECT id, user_id, type, title, message, link, is_read, created_at
            FROM user_notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "type": r["type"],
                "title": r["title"],
                "message": r["message"],
                "link": r["link"],
                "is_read": bool(r["is_read"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    async def get_unread_count(self, user_id: int) -> int:
        cursor = await self._conn.execute(
            """
            SELECT COUNT(*) FROM user_notifications
            WHERE user_id = ? AND is_read = 0
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        cursor = await self._conn.execute(
            """
            UPDATE user_notifications
            SET is_read = 1
            WHERE id = ? AND user_id = ?
            """,
            (notification_id, user_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def mark_all_as_read(self, user_id: int) -> int:
        cursor = await self._conn.execute(
            """
            UPDATE user_notifications
            SET is_read = 1
            WHERE user_id = ? AND is_read = 0
            """,
            (user_id,),
        )
        await self._conn.commit()
        return cursor.rowcount
