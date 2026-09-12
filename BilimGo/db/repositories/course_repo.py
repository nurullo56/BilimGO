from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class Course:
    id: int
    title: str
    owner_node_id: int | None
    base_price: float
    status: str
    description: str | None = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Course:
        return cls(
            id=row["id"],
            title=row["title"],
            owner_node_id=row["owner_node_id"],
            base_price=row["base_price"],
            status=row["status"],
            description=row["description"] if "description" in row.keys() else None,
        )


class CourseRepository(BaseRepository):
    async def get_by_id(self, course_id: int) -> Course | None:
        cursor = await self._conn.execute(
            "SELECT * FROM courses WHERE id = ?", (course_id,)
        )
        row = await cursor.fetchone()
        return Course.from_row(row) if row else None

    async def list_published(self) -> list[Course]:
        cursor = await self._conn.execute(
            "SELECT * FROM courses WHERE status = 'published' ORDER BY id DESC"
        )
        rows = await cursor.fetchall()
        return [Course.from_row(r) for r in rows]
