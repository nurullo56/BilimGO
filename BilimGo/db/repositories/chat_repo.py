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

    async def get_room_by_id(self, room_id: int) -> int | None:
        """Xona ID si bo'yicha mavjudligini tekshiradi."""
        cursor = await self._conn.execute("SELECT id FROM chat_rooms WHERE id = ?", (room_id,))
        row = await cursor.fetchone()
        return row["id"] if row else None

    async def get_first_room_for_cabinet(self, cabinet_id: int) -> int | None:
        """Kabinet ID si bo'yicha unga biriktirilgan birinchi xona ID sini oladi."""
        cursor = await self._conn.execute(
            "SELECT id FROM chat_rooms WHERE cabinet_id = ? LIMIT 1", (cabinet_id,)
        )
        row = await cursor.fetchone()
        return row["id"] if row else None

    async def resolve_or_create_room(self, clean_num: int, user_id: int) -> int:
        """
        Xona yoki kabinet ID si bo'yicha aniqlaydi, yo'q bo'lsa yangi xona ochadi
        va foydalanuvchini avtomatik a'zo qilib qo'yadi.
        """
        # 1. To'g'ridan-to'g'ri xona ID bo'yicha tekshirish
        room_id = await self.get_room_by_id(clean_num)
        if not room_id:
            # 2. Kabinet ID bo'yicha tekshirish
            room_id = await self.get_first_room_for_cabinet(clean_num)
            if not room_id:
                # 3. Agar mavjud bo'lmasa, ushbu kabinet uchun yangi xona yaratish
                cursor = await self._conn.execute(
                    "INSERT INTO chat_rooms (cabinet_id, course_id) VALUES (?, 1)",
                    (clean_num,),
                )
                await self._conn.commit()
                room_id = cursor.lastrowid

        # Foydalanuvchini xona a'zosi qilib qo'yish
        await self._conn.execute(
            "INSERT INTO chat_room_members (room_id, user_id) VALUES (?, ?) ON CONFLICT(room_id, user_id) DO NOTHING",
            (room_id, user_id),
        )
        await self._conn.commit()
        return room_id

    async def list_messages_with_users(
        self, room_id: int, after_id: int = 0, limit: int = 100
    ) -> list[dict]:
        """Xonadagi xabarlarni yuboruvchining ismi va roli bilan birga oladi."""
        cursor = await self._conn.execute(
            """
            SELECT m.id, m.sender_id, m.content, m.sent_at,
                   u.full_name, u.role, u.telegram_id
            FROM chat_messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.room_id = ? AND m.id > ?
            ORDER BY m.id ASC
            LIMIT ?
            """,
            (room_id, after_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

