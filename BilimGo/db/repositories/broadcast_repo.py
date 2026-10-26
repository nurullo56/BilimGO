from __future__ import annotations
from typing import Optional
from db.database import database

class BroadcastRepository:
    def __init__(self) -> None:
        self.db = database

    async def create_broadcast(self, admin_id: int, target_type: str, total_count: int) -> int:
        await self.db.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor = await self.db.conn.execute(
            "INSERT INTO broadcasts (admin_id, target_type, total_count, status) VALUES (?, ?, ?, 'in_progress')",
            (admin_id, target_type, total_count),
        )
        await self.db.conn.commit()
        return cursor.lastrowid

    async def update_broadcast_status(self, broadcast_id: int, sent_count: int, failed_count: int, status: str = "completed") -> None:
        await self.db.conn.execute(
            "UPDATE broadcasts SET sent_count = ?, failed_count = ?, status = ? WHERE id = ?",
            (sent_count, failed_count, status, broadcast_id),
        )
        await self.db.conn.commit()
