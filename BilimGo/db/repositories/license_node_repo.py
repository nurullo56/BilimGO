from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class LicenseNode:
    id: int
    parent_id: int | None
    owner_user_id: int
    course_id: int | None
    royalty_percent: float
    stage: str
    status: str
    stage_started_at: str | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> LicenseNode:
        keys = row.keys()
        return cls(
            id=row["id"],
            parent_id=row["parent_id"],
            owner_user_id=row["owner_user_id"],
            course_id=row["course_id"],
            royalty_percent=row["royalty_percent"],
            stage=row["stage"],
            status=row["status"],
            stage_started_at=row["stage_started_at"] if "stage_started_at" in keys else None,
            created_at=row["created_at"] if "created_at" in keys else None,
        )


class LicenseNodeRepository(BaseRepository):
    async def get_by_id(self, node_id: int) -> LicenseNode | None:
        cursor = await self._conn.execute(
            "SELECT * FROM license_nodes WHERE id = ?", (node_id,)
        )
        row = await cursor.fetchone()
        return LicenseNode.from_row(row) if row else None

    async def get_ancestors(self, node_id: int) -> list[LicenseNode]:
        """Berilgan tugundan ildizgacha bo'lgan zanjirni (o'zidan tashqari)
        recursive CTE orqali qaytaradi, eng yaqin otadan boshlab."""
        cursor = await self._conn.execute(
            """
            WITH RECURSIVE ancestors AS (
                SELECT parent_id AS id FROM license_nodes WHERE id = ?
                UNION ALL
                SELECT ln.parent_id
                FROM license_nodes ln
                JOIN ancestors a ON ln.id = a.id
                WHERE ln.parent_id IS NOT NULL
            )
            SELECT ln.* FROM license_nodes ln
            JOIN ancestors a ON ln.id = a.id
            WHERE a.id IS NOT NULL
            """,
            (node_id,),
        )
        rows = await cursor.fetchall()
        return [LicenseNode.from_row(r) for r in rows]

    async def update_stage(self, node_id: int, new_stage: str, autocommit: bool = True) -> None:
        await self._conn.execute(
            """
            UPDATE license_nodes
            SET stage = ?, stage_started_at = datetime('now')
            WHERE id = ?
            """,
            (new_stage, node_id),
        )
        if autocommit:
            await self._conn.commit()

    async def update_status(self, node_id: int, new_status: str, autocommit: bool = True) -> None:
        await self._conn.execute(
            """
            UPDATE license_nodes
            SET status = ?
            WHERE id = ?
            """,
            (new_status, node_id),
        )
        if autocommit:
            await self._conn.commit()

    async def get_by_owner_id(self, owner_user_id: int) -> LicenseNode | None:
        cursor = await self._conn.execute(
            "SELECT * FROM license_nodes WHERE owner_user_id = ? ORDER BY id ASC LIMIT 1",
            (owner_user_id,),
        )
        row = await cursor.fetchone()
        return LicenseNode.from_row(row) if row else None

    async def is_limit_expired(self, node_id: int) -> bool:
        cursor = await self._conn.execute(
            """
            SELECT stage_started_at <= datetime('now', '-15 days') AS is_expired
            FROM license_nodes WHERE id = ?
            """,
            (node_id,),
        )
        row = await cursor.fetchone()
        return bool(row["is_expired"]) if row and row["is_expired"] is not None else False
