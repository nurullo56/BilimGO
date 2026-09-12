from __future__ import annotations

from db.repositories.base import BaseRepository


class RoyaltyLedgerRepository(BaseRepository):
    async def create_entry(
        self,
        sale_id: int,
        node_id: int,
        percent_applied: float,
        amount: float,
        autocommit: bool = True,
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO royalty_ledger (sale_id, node_id, percent_applied, amount)
            VALUES (?, ?, ?, ?)
            """,
            (sale_id, node_id, percent_applied, amount),
        )
        if autocommit:
            await self._conn.commit()

    async def exists_for_sale(self, sale_id: int) -> bool:
        """Idempotentlik uchun — bitta sale uchun royalty ikki marta yozilmasligi kerak."""
        cursor = await self._conn.execute(
            "SELECT 1 FROM royalty_ledger WHERE sale_id = ? LIMIT 1", (sale_id,)
        )
        return await cursor.fetchone() is not None

    async def unsettled_total_for_node(self, node_id: int) -> float:
        cursor = await self._conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM royalty_ledger
            WHERE node_id = ? AND settled_at IS NULL
            """,
            (node_id,),
        )
        row = await cursor.fetchone()
        return row["total"]

    async def settle_for_node(self, node_id: int) -> None:
        await self._conn.execute(
            """
            UPDATE royalty_ledger
            SET settled_at = datetime('now')
            WHERE node_id = ? AND settled_at IS NULL
            """,
            (node_id,),
        )
        await self._conn.commit()

    async def unsettled_info_for_child_node(self, child_node_id: int) -> dict:
        """Kichik mentorning (child_node) sotgan va hali royaltisi yechilmagan savdolari soni va summasi."""
        cursor = await self._conn.execute(
            """
            SELECT COUNT(rl.id) AS sales_count, COALESCE(SUM(rl.amount), 0) AS total_amount
            FROM royalty_ledger rl
            JOIN sales s ON s.id = rl.sale_id
            WHERE s.license_node_id = ? AND rl.settled_at IS NULL
            """,
            (child_node_id,),
        )
        row = await cursor.fetchone()
        return {
            "sales_count": row["sales_count"] if row else 0,
            "total_amount": float(row["total_amount"]) if row else 0.0,
        }

    async def settle_for_child_node(self, child_node_id: int) -> None:
        """Kichik mentorning qarz royaltilarini to'langan deb belgilash."""
        await self._conn.execute(
            """
            UPDATE royalty_ledger
            SET settled_at = datetime('now')
            WHERE id IN (
                SELECT rl.id FROM royalty_ledger rl
                JOIN sales s ON s.id = rl.sale_id
                WHERE s.license_node_id = ? AND rl.settled_at IS NULL
            )
            """,
            (child_node_id,),
        )
        await self._conn.commit()

    async def record_auto_settlement(
        self,
        node_id: int,
        mentor_id: int,
        amount: float,
        sales_count: int,
        provider: str,
        external_txn_id: str,
        status: str = "success",
    ) -> None:
        """Avto-yechib olish natijasini qayd etish."""
        await self._conn.execute(
            """
            INSERT INTO royalty_auto_settlements (node_id, mentor_id, amount, sales_count, provider, external_txn_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (node_id, mentor_id, amount, sales_count, provider, str(external_txn_id), status),
        )
        await self._conn.commit()
