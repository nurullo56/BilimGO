from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class PaymeTransaction:
    id: str
    sale_id: int
    amount: float
    state: int
    create_time: int
    perform_time: int
    cancel_time: int
    reason: int | None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> PaymeTransaction:
        return cls(
            id=row["id"],
            sale_id=row["sale_id"],
            amount=row["amount"],
            state=row["state"],
            create_time=row["create_time"],
            perform_time=row["perform_time"],
            cancel_time=row["cancel_time"],
            reason=row["reason"],
        )


class PaymeTransactionRepository(BaseRepository):
    async def get_by_id(self, payme_id: str) -> PaymeTransaction | None:
        cursor = await self._conn.execute(
            "SELECT * FROM payme_transactions WHERE id = ?", (payme_id,)
        )
        row = await cursor.fetchone()
        return PaymeTransaction.from_row(row) if row else None

    async def create(self, payme_id: str, sale_id: int, amount: float, create_time: int) -> None:
        await self._conn.execute(
            """
            INSERT INTO payme_transactions (id, sale_id, amount, state, create_time)
            VALUES (?, ?, ?, 1, ?)
            """,
            (payme_id, sale_id, amount, create_time),
        )
        await self._conn.commit()

    async def mark_performed(self, payme_id: str, perform_time: int) -> None:
        await self._conn.execute(
            "UPDATE payme_transactions SET state = 2, perform_time = ? WHERE id = ?",
            (perform_time, payme_id),
        )
        await self._conn.commit()

    async def mark_cancelled(
        self, payme_id: str, cancel_time: int, reason: int, new_state: int
    ) -> None:
        await self._conn.execute(
            """
            UPDATE payme_transactions
            SET state = ?, cancel_time = ?, reason = ?
            WHERE id = ?
            """,
            (new_state, cancel_time, reason, payme_id),
        )
        await self._conn.commit()
