from __future__ import annotations
from typing import Any, List, Optional
from db.database import database

class AdminRepository:
    def __init__(self) -> None:
        self.db = database

    async def get_overall_stats(self) -> dict[str, Any]:
        c_users = await self.db.conn.execute("SELECT COUNT(*) as cnt FROM users")
        u_count = (await c_users.fetchone())["cnt"]
        c_sales = await self.db.conn.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM sales WHERE status = 'paid'")
        s_row = await c_sales.fetchone()
        return {
            "total_users": u_count,
            "total_sales_count": s_row["cnt"],
            "total_revenue": s_row["total"],
        }
