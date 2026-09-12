from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class DeliveryToken:
    id: int
    user_id: int
    lesson_id: int
    token_hash: str
    expires_at: str
    used_at: str | None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> DeliveryToken:
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            lesson_id=row["lesson_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            used_at=row["used_at"],
        )

    def is_valid(self) -> bool:
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() < expires


class DeliveryTokenRepository(BaseRepository):
    async def create(
        self, user_id: int, lesson_id: int, token_hash: str, expires_at: str
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO delivery_tokens (user_id, lesson_id, token_hash, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, lesson_id, token_hash, expires_at),
        )
        await self._conn.commit()

    async def get_by_hash(self, token_hash: str) -> DeliveryToken | None:
        cursor = await self._conn.execute(
            "SELECT * FROM delivery_tokens WHERE token_hash = ?", (token_hash,)
        )
        row = await cursor.fetchone()
        return DeliveryToken.from_row(row) if row else None

    async def mark_activated(self, token_hash: str) -> None:
        """Birinchi marta ishlatilganda used_at ni belgilaydi (audit uchun).
        Token o'zi expires_at gacha amal qiladi — video streaming ko'p
        Range so'rov yuborishi mumkinligi uchun bir martalik emas."""
        await self._conn.execute(
            """
            UPDATE delivery_tokens
            SET used_at = datetime('now')
            WHERE token_hash = ? AND used_at IS NULL
            """,
            (token_hash,),
        )
        await self._conn.commit()
