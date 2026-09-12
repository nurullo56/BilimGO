from __future__ import annotations

from db.repositories.base import BaseRepository


class ClickTransactionRepository(BaseRepository):
    async def create_if_absent(
        self, click_trans_id: str, sale_id: int, prepare_id: str, amount: float
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO click_transactions (click_trans_id, sale_id, prepare_id, amount, status)
            VALUES (?, ?, ?, ?, 'prepared')
            ON CONFLICT(click_trans_id) DO NOTHING
            """,
            (click_trans_id, sale_id, prepare_id, amount),
        )
        await self._conn.commit()

    async def mark_confirmed(self, click_trans_id: str) -> None:
        await self._conn.execute(
            "UPDATE click_transactions SET status = 'confirmed' WHERE click_trans_id = ?",
            (click_trans_id,),
        )
        await self._conn.commit()
