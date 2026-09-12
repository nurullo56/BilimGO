from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class Lesson:
    id: int
    course_id: int
    title: str
    order_index: int
    source_channel_id: int | None
    source_message_id: int | None
    duration_sec: int | None
    is_free_preview: bool

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Lesson:
        return cls(
            id=row["id"],
            course_id=row["course_id"],
            title=row["title"],
            order_index=row["order_index"],
            source_channel_id=row["source_channel_id"],
            source_message_id=row["source_message_id"],
            duration_sec=row["duration_sec"],
            is_free_preview=bool(row["is_free_preview"]),
        )


class LessonRepository(BaseRepository):
    async def get_by_id(self, lesson_id: int) -> Lesson | None:
        cursor = await self._conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
        )
        row = await cursor.fetchone()
        return Lesson.from_row(row) if row else None

    async def list_by_course(self, course_id: int) -> list[Lesson]:
        cursor = await self._conn.execute(
            "SELECT * FROM lessons WHERE course_id = ? ORDER BY order_index",
            (course_id,),
        )
        rows = await cursor.fetchall()
        return [Lesson.from_row(r) for r in rows]
