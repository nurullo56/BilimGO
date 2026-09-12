from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import aiosqlite

from db.repositories.base import BaseRepository

UserRole = Literal["student", "mentor", "admin"]
UserStatus = Literal["active", "blocked"]


@dataclass(slots=True)
class User:
    id: int
    telegram_id: int
    full_name: str | None
    phone: str | None
    role: UserRole
    status: UserStatus
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> User:
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            full_name=row["full_name"],
            phone=row["phone"],
            role=row["role"],
            status=row["status"],
            created_at=row["created_at"],
        )


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: int) -> User | None:
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None

    async def get_or_create(
        self, telegram_id: int, full_name: str | None = None
    ) -> User:
        await self._conn.execute(
            """
            INSERT INTO users (telegram_id, full_name)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO NOTHING
            """,
            (telegram_id, full_name),
        )
        await self._conn.commit()

        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            raise NotFoundError(f"User yaratilmadi yoki topilmadi: tg_id={telegram_id}")
        return user

    async def update_role(self, user_id: int, role: UserRole) -> None:
        await self._conn.execute(
            "UPDATE users SET role = ? WHERE id = ?", (role, user_id)
        )
        await self._conn.commit()

    async def update_phone(self, user_id: int, phone: str) -> None:
        await self._conn.execute(
            "UPDATE users SET phone = ? WHERE id = ?", (phone, user_id)
        )
        await self._conn.commit()

    async def update_profile(
        self, user_id: int, full_name: str | None = None, phone: str | None = None
    ) -> None:
        updates = []
        params = []
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if updates:
            params.append(user_id)
            await self._conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params)
            )
            await self._conn.commit()

    async def set_status(self, user_id: int, status: UserStatus) -> None:
        await self._conn.execute(
            "UPDATE users SET status = ? WHERE id = ?", (status, user_id)
        )
        await self._conn.commit()