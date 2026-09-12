from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class Sale:
    id: int
    student_id: int
    course_id: int
    license_node_id: int
    amount: float
    payment_provider: str
    payment_status: str
    external_txn_id: str | None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Sale:
        return cls(
            id=row["id"],
            student_id=row["student_id"],
            course_id=row["course_id"],
            license_node_id=row["license_node_id"],
            amount=row["amount"],
            payment_provider=row["payment_provider"],
            payment_status=row["payment_status"],
            external_txn_id=row["external_txn_id"],
        )


class SaleRepository(BaseRepository):
    async def create_pending(
        self,
        student_id: int,
        course_id: int,
        license_node_id: int,
        amount: float,
        payment_provider: str,
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO sales (student_id, course_id, license_node_id, amount, payment_provider)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, course_id, license_node_id, amount, payment_provider),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_by_id(self, sale_id: int) -> Sale | None:
        cursor = await self._conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
        row = await cursor.fetchone()
        return Sale.from_row(row) if row else None

    async def mark_paid(self, sale_id: int, external_txn_id: str) -> None:
        await self._conn.execute(
            """
            UPDATE sales
            SET payment_status = 'paid', external_txn_id = ?, paid_at = datetime('now')
            WHERE id = ? AND payment_status = 'pending'
            """,
            (external_txn_id, sale_id),
        )
        await self._conn.commit()

    async def mark_failed(self, sale_id: int) -> None:
        await self._conn.execute(
            "UPDATE sales SET payment_status = 'failed' WHERE id = ? AND payment_status = 'pending'",
            (sale_id,),
        )
        await self._conn.commit()

    async def mark_refunded(self, sale_id: int) -> None:
        await self._conn.execute(
            "UPDATE sales SET payment_status = 'refunded' WHERE id = ? AND payment_status = 'paid'",
            (sale_id,),
        )
        await self._conn.commit()
