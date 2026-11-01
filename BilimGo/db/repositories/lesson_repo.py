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

    async def get_source_post_text(
        self, source_channel_id: int | None, source_message_id: int | None
    ) -> str | None:
        """Darsning Telegram kanalidagi manba postidan matnli materialini xavfsiz oladi."""
        if not source_channel_id or not source_message_id:
            return None
        try:
            import sqlite3
            from pathlib import Path
            from core.config import settings

            candidate_userbot_dbs = [
                settings.paths.userbot_db_path,
                Path("C:/Users/Acer/Downloads/BilimGoUserBot/BilimGoUserBot/userbot_database.db"),
                Path(__file__).resolve().parents[4] / "BilimGoUserBot" / "BilimGoUserBot" / "userbot_database.db",
                Path(__file__).resolve().parents[3] / "BilimGoUserBot" / "BilimGoUserBot" / "userbot_database.db",
            ]
            userbot_db_path = None
            for db_p in candidate_userbot_dbs:
                if db_p and db_p.exists():
                    userbot_db_path = db_p
                    break
            if not userbot_db_path:
                return None
            with sqlite3.connect(userbot_db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT text FROM posts WHERE channel_id = ? AND message_id = ?",
                    (source_channel_id, source_message_id),
                ).fetchone()
                if row and row["text"] and len(row["text"].strip()) > 20:
                    return row["text"].strip()
        except Exception:
            pass
        return None

