from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class ChatMessage:
    id: int
    room_id: int
    sender_id: int
    content: str
    sent_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> ChatMessage:
        return cls(
            id=row["id"],
            room_id=row["room_id"],
            sender_id=row["sender_id"],
            content=row["content"],
            sent_at=row["sent_at"],
        )


class ChatRepository(BaseRepository):
    async def get_room(self, cabinet_id: int, course_id: int) -> int | None:
        cursor = await self._conn.execute(
            "SELECT id FROM chat_rooms WHERE cabinet_id = ? AND course_id = ?",
            (cabinet_id, course_id),
        )
        row = await cursor.fetchone()
        return row["id"] if row else None

    async def create_room(self, cabinet_id: int, course_id: int) -> int:
        await self._conn.execute(
            """
            INSERT INTO chat_rooms (cabinet_id, course_id)
            VALUES (?, ?)
            ON CONFLICT(cabinet_id, course_id) DO NOTHING
            """,
            (cabinet_id, course_id),
        )
        await self._conn.commit()
        room_id = await self.get_room(cabinet_id, course_id)
        assert room_id is not None
        return room_id

    async def add_room_member(self, room_id: int, user_id: int) -> None:
        await self._conn.execute(
            """
            INSERT INTO chat_room_members (room_id, user_id)
            VALUES (?, ?)
            ON CONFLICT(room_id, user_id) DO NOTHING
            """,
            (room_id, user_id),
        )
        await self._conn.commit()

    async def is_room_member(self, room_id: int, user_id: int) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM chat_room_members WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        )
        return await cursor.fetchone() is not None

    async def send_message(self, room_id: int, sender_id: int, content: str) -> ChatMessage:
        cursor = await self._conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, content) VALUES (?, ?, ?)",
            (room_id, sender_id, content),
        )
        await self._conn.commit()
        message_cursor = await self._conn.execute(
            "SELECT * FROM chat_messages WHERE id = ?", (cursor.lastrowid,)
        )
        row = await message_cursor.fetchone()
        assert row is not None
        return ChatMessage.from_row(row)

    async def list_messages_after(
        self, room_id: int, after_id: int, limit: int = 100
    ) -> list[ChatMessage]:
        cursor = await self._conn.execute(
            """
            SELECT * FROM chat_messages
            WHERE room_id = ? AND id > ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (room_id, after_id, limit),
        )
        rows = await cursor.fetchall()
        return [ChatMessage.from_row(r) for r in rows]

    async def update_last_read(self, room_id: int, user_id: int, message_id: int) -> None:
        await self._conn.execute(
            """
            UPDATE chat_room_members
            SET last_read_message_id = ?
            WHERE room_id = ? AND user_id = ?
            """,
            (message_id, room_id, user_id),
        )
        await self._conn.commit()

    async def list_rooms_for_cabinet(self, cabinet_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT cr.id, cr.cabinet_id, cr.course_id, c.title AS course_title
            FROM chat_rooms cr
            LEFT JOIN courses c ON c.id = cr.course_id
            WHERE cr.cabinet_id = ?
            """,
            (cabinet_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
