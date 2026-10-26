from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MentorApplication:
    id: int
    user_id: int
    full_name: str
    phone: str
    telegram_username: str | None
    course_direction: str
    experience_bio: str
    status: str
    payment_amount: int
    receipt_photo_id: str | None
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> MentorApplication:
        keys = row.keys()
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            full_name=row["full_name"],
            phone=row["phone"],
            telegram_username=row["telegram_username"] if "telegram_username" in keys else None,
            course_direction=row["course_direction"] if "course_direction" in keys else "",
            experience_bio=row["experience_bio"] if "experience_bio" in keys else "",
            status=row["status"],
            payment_amount=row["payment_amount"] if ("payment_amount" in keys and row["payment_amount"]) else int(os.getenv("MENTOR_PRICE", "949000")),
            receipt_photo_id=row["receipt_photo_id"] if "receipt_photo_id" in keys else None,
            created_at=row["created_at"],
        )


class MentorApplicationRepository(BaseRepository):
    async def create(
        self,
        user_id: int,
        full_name: str,
        phone: str,
        course_direction: str,
        experience_bio: str,
        telegram_username: str | None = None,
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO mentor_applications (user_id, full_name, phone, telegram_username, course_direction, experience_bio, status, payment_amount)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (user_id, full_name, phone, telegram_username, course_direction, experience_bio, int(os.getenv('MENTOR_PRICE', '949000'))),
        )
        await self._conn.commit()
        app_id = cursor.lastrowid
        logger.info(
            "Yangi mentorlik arizasi saqlandi: id=%s, user_id=%s, ism=%s, yo'nalish=%s",
            app_id,
            user_id,
            full_name,
            course_direction,
        )
        return app_id

    async def get_latest_by_user_id(self, user_id: int) -> MentorApplication | None:
        cursor = await self._conn.execute(
            """
            SELECT * FROM mentor_applications
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return MentorApplication.from_row(row) if row else None

    async def get_by_id(self, app_id: int) -> MentorApplication | None:
        cursor = await self._conn.execute(
            """
            SELECT * FROM mentor_applications
            WHERE id = ?
            """,
            (app_id,),
        )
        row = await cursor.fetchone()
        return MentorApplication.from_row(row) if row else None

    async def list_all(self) -> list[MentorApplication]:
        cursor = await self._conn.execute(
            """
            SELECT * FROM mentor_applications
            ORDER BY id DESC
            """
        )
        rows = await cursor.fetchall()
        return [MentorApplication.from_row(r) for r in rows]

    async def update_status(self, app_id: int, status: str) -> None:
        await self._conn.execute(
            """
            UPDATE mentor_applications
            SET status = ?
            WHERE id = ?
            """,
            (status, app_id),
        )
        await self._conn.commit()
        logger.info("Mentorlik arizasi holati yangilandi: id=%s, status=%s", app_id, status)
