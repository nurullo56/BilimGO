from __future__ import annotations

from dataclasses import dataclass
import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class MentorCard:
    id: int
    mentor_id: int
    provider: str
    card_token: str
    card_number_masked: str | None
    card_expire: str | None
    is_active: bool
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> MentorCard:
        return cls(
            id=row["id"],
            mentor_id=row["mentor_id"],
            provider=row["provider"],
            card_token=row["card_token"],
            card_number_masked=row["card_number_masked"],
            card_expire=row["card_expire"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )


class MentorCardRepository(BaseRepository):
    async def save_card(
        self,
        mentor_id: int,
        provider: str,
        card_token: str,
        card_number_masked: str | None = None,
        card_expire: str | None = None,
    ) -> MentorCard:
        await self._conn.execute(
            """
            INSERT INTO mentor_cards (mentor_id, provider, card_token, card_number_masked, card_expire, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(mentor_id, provider) DO UPDATE SET
                card_token = excluded.card_token,
                card_number_masked = excluded.card_number_masked,
                card_expire = excluded.card_expire,
                is_active = 1
            """,
            (mentor_id, provider, card_token, card_number_masked, card_expire),
        )
        await self._conn.commit()
        card = await self.get_active_card(mentor_id, provider)
        assert card is not None
        return card

    async def get_active_card(
        self, mentor_id: int, provider: str | None = None
    ) -> MentorCard | None:
        query = "SELECT * FROM mentor_cards WHERE mentor_id = ? AND is_active = 1"
        params: list = [mentor_id]
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        query += " ORDER BY id DESC LIMIT 1"

        cursor = await self._conn.execute(query, params)
        row = await cursor.fetchone()
        return MentorCard.from_row(row) if row else None

    async def deactivate_card(self, card_id: int) -> None:
        await self._conn.execute(
            "UPDATE mentor_cards SET is_active = 0 WHERE id = ?", (card_id,)
        )
        await self._conn.commit()
