from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class Cabinet:
    id: int
    owner_node_id: int
    display_name: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Cabinet:
        return cls(
            id=row["id"],
            owner_node_id=row["owner_node_id"],
            display_name=row["display_name"],
        )


class CabinetRepository(BaseRepository):
    async def get_by_owner_node(self, owner_node_id: int) -> Cabinet | None:
        cursor = await self._conn.execute(
            "SELECT * FROM cabinets WHERE owner_node_id = ?", (owner_node_id,)
        )
        row = await cursor.fetchone()
        return Cabinet.from_row(row) if row else None

    async def create(self, owner_node_id: int, display_name: str) -> Cabinet:
        existing = await self.get_by_owner_node(owner_node_id)
        if existing:
            return existing

        await self._conn.execute(
            """
            INSERT INTO cabinets (owner_node_id, display_name)
            VALUES (?, ?)
            """,
            (owner_node_id, display_name),
        )
        await self._conn.commit()
        cabinet = await self.get_by_owner_node(owner_node_id)
        assert cabinet is not None
        return cabinet

    async def add_member(self, cabinet_id: int, user_id: int, role: str) -> None:
        await self._conn.execute(
            """
            INSERT INTO cabinet_members (cabinet_id, user_id, role_in_cabinet)
            VALUES (?, ?, ?)
            ON CONFLICT(cabinet_id, user_id) DO NOTHING
            """,
            (cabinet_id, user_id, role),
        )
        await self._conn.commit()

    async def is_member(self, cabinet_id: int, user_id: int) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM cabinet_members WHERE cabinet_id = ? AND user_id = ?",
            (cabinet_id, user_id),
        )
        return await cursor.fetchone() is not None

    async def list_students(self, cabinet_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT u.id, u.telegram_id, u.full_name, cm.joined_at
            FROM cabinet_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.cabinet_id = ? AND cm.role_in_cabinet = 'student'
            ORDER BY cm.joined_at DESC
            """,
            (cabinet_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def count_students(self, cabinet_id: int) -> int:
        cursor = await self._conn.execute(
            """
            SELECT COUNT(*) as count
            FROM cabinet_members
            WHERE cabinet_id = ? AND role_in_cabinet = 'student'
            """,
            (cabinet_id,),
        )
        row = await cursor.fetchone()
        return row["count"] if row else 0

    async def list_my_cabinets(self, user_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT c.id, c.display_name, COALESCE(cm.role_in_cabinet, 'member') as role_in_cabinet
            FROM cabinets c
            LEFT JOIN cabinet_members cm ON cm.cabinet_id = c.id AND cm.user_id = ?
            ORDER BY c.id DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
