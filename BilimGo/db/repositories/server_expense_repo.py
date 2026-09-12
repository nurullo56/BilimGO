from __future__ import annotations

from dataclasses import dataclass
import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class ServerExpense:
    id: int
    mentor_id: int
    student_id: int | None
    expense_type: str
    units_used: float
    unit_name: str
    cost_sum: float
    description: str | None
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> ServerExpense:
        return cls(
            id=row["id"],
            mentor_id=row["mentor_id"],
            student_id=row["student_id"],
            expense_type=row["expense_type"],
            units_used=float(row["units_used"]),
            unit_name=row["unit_name"],
            cost_sum=float(row["cost_sum"]),
            description=row["description"],
            created_at=row["created_at"],
        )


class ServerExpenseRepository(BaseRepository):
    async def record_expense(
        self,
        mentor_id: int,
        student_id: int | None,
        expense_type: str,
        units_used: float = 1.0,
        unit_name: str = "view",
        cost_sum: float = 0.0,
        description: str = "",
    ) -> ServerExpense:
        cursor = await self._conn.execute(
            """
            INSERT INTO server_expense_usage (mentor_id, student_id, expense_type, units_used, unit_name, cost_sum, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (mentor_id, student_id, expense_type, units_used, unit_name, cost_sum, description),
        )
        await self._conn.commit()
        row_id = cursor.lastrowid
        assert row_id is not None

        c2 = await self._conn.execute("SELECT * FROM server_expense_usage WHERE id = ?", (row_id,))
        row = await c2.fetchone()
        assert row is not None
        return ServerExpense.from_row(row)

    async def get_mentor_summary(self, mentor_id: int) -> dict:
        cursor = await self._conn.execute(
            """
            SELECT 
                COUNT(id) AS total_events,
                COALESCE(SUM(cost_sum), 0.0) AS total_cost_sum,
                COALESCE(SUM(CASE WHEN expense_type = 'video_bandwidth' THEN units_used ELSE 0 END), 0) AS total_video_views,
                COALESCE(SUM(CASE WHEN expense_type = 'video_bandwidth' THEN cost_sum ELSE 0 END), 0.0) AS video_bandwidth_cost,
                COALESCE(SUM(CASE WHEN expense_type = 'hosting_maintenance' THEN cost_sum ELSE 0 END), 0.0) AS hosting_cost,
                COALESCE(SUM(CASE WHEN expense_type = 'active_student' THEN cost_sum ELSE 0 END), 0.0) AS active_student_cost
            FROM server_expense_usage
            WHERE mentor_id = ?
            """,
            (mentor_id,),
        )
        row = await cursor.fetchone()
        return {
            "total_events": row["total_events"] if row else 0,
            "total_cost_sum": float(row["total_cost_sum"]) if row else 0.0,
            "total_video_views": int(row["total_video_views"]) if row else 0,
            "video_bandwidth_cost": float(row["video_bandwidth_cost"]) if row else 0.0,
            "hosting_cost": float(row["hosting_cost"]) if row else 0.0,
            "active_student_cost": float(row["active_student_cost"]) if row else 0.0,
        }

    async def list_mentor_recent(self, mentor_id: int, limit: int = 20) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT seu.id, seu.expense_type, seu.units_used, seu.unit_name,
                   seu.cost_sum, seu.description, seu.created_at,
                   u.full_name AS student_name
            FROM server_expense_usage seu
            LEFT JOIN users u ON u.id = seu.student_id
            WHERE seu.mentor_id = ?
            ORDER BY seu.id DESC
            LIMIT ?
            """,
            (mentor_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
