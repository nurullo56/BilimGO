from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class MentorUserbot:
    id: int
    mentor_id: int
    status: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> MentorUserbot:
        return cls(id=row["id"], mentor_id=row["mentor_id"], status=row["status"])


class MentorUserbotRepository(BaseRepository):
    async def get_by_mentor(self, mentor_id: int) -> MentorUserbot | None:
        cursor = await self._conn.execute(
            "SELECT * FROM mentor_userbots WHERE mentor_id = ?", (mentor_id,)
        )
        row = await cursor.fetchone()
        return MentorUserbot.from_row(row) if row else None

    async def upsert_connected(
        self, mentor_id: int, session_string: str, phone_number: str
    ) -> MentorUserbot:
        await self._conn.execute(
            """
            INSERT INTO mentor_userbots (mentor_id, session_string, phone_number, status, connected_at)
            VALUES (?, ?, ?, 'connected', datetime('now'))
            ON CONFLICT(mentor_id) DO UPDATE SET
                session_string = excluded.session_string,
                phone_number = excluded.phone_number,
                status = 'connected',
                connected_at = datetime('now')
            """,
            (mentor_id, session_string, phone_number),
        )
        await self._conn.commit()
        result = await self.get_by_mentor(mentor_id)
        assert result is not None
        return result

    async def mark_disconnected(self, mentor_id: int) -> None:
        await self._conn.execute(
            "UPDATE mentor_userbots SET status = 'disconnected' WHERE mentor_id = ?",
            (mentor_id,),
        )
        await self._conn.commit()
