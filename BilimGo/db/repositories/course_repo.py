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
    created_at: str | None = None
    is_waitlist: bool = False
    image_url: str | None = None
    notice_text: str | None = None
    syllabus: str | None = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Course:
        return cls(
            id=row["id"],
            title=row["title"],
            owner_node_id=row["owner_node_id"],
            base_price=row["base_price"],
            status=row["status"],
            description=row["description"] if "description" in row.keys() else None,
            created_at=row["created_at"] if "created_at" in row.keys() else None,
            is_waitlist=bool(row["is_waitlist"]) if "is_waitlist" in row.keys() and row["is_waitlist"] is not None else False,
            image_url=row["image_url"] if "image_url" in row.keys() else None,
            notice_text=row["notice_text"] if "notice_text" in row.keys() else None,
            syllabus=row["syllabus"] if "syllabus" in row.keys() else None,
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
            "SELECT * FROM courses WHERE status = 'published' ORDER BY id ASC"
        )
        rows = await cursor.fetchall()
        return [Course.from_row(r) for r in rows]

    async def update_waitlist_status(self, course_id: int, is_waitlist: bool) -> None:
        """Kursning kutish ro'yxati (waitlist) holatini yangilaydi."""
        await self._conn.execute(
            "UPDATE courses SET is_waitlist = ? WHERE id = ?",
            (1 if is_waitlist else 0, course_id),
        )
        await self._conn.commit()

    async def update_notice_text(self, course_id: int, notice_text: str | None) -> None:
        """Kursning maxsus e'lon / chegirma matnini yangilaydi."""
        await self._conn.execute(
            "UPDATE courses SET notice_text = ? WHERE id = ?",
            (notice_text, course_id),
        )
        await self._conn.commit()

    async def update_image_url(self, course_id: int, image_url: str | None) -> None:
        """Kursning muqova rasmi (URL) ni yangilaydi."""
        await self._conn.execute(
            "UPDATE courses SET image_url = ? WHERE id = ?",
            (image_url, course_id),
        )
        await self._conn.commit()
