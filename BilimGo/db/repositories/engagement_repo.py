from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class NudgeCampaign:
    id: int
    user_id: int
    current_step: int
    status: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> NudgeCampaign:
        return cls(
            id=row["id"], user_id=row["user_id"],
            current_step=row["current_step"], status=row["status"],
        )


class EngagementRepository(BaseRepository):
    async def touch(self, user_id: int) -> None:
        await self._conn.execute(
            """
            INSERT INTO engagement_activity (user_id, last_seen_at)
            VALUES (?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET last_seen_at = datetime('now')
            """,
            (user_id,),
        )
        await self._conn.commit()

    async def list_inactive_since(self, hours: int) -> list[int]:
        cursor = await self._conn.execute(
            """
            SELECT ea.user_id FROM engagement_activity ea
            JOIN users u ON u.id = ea.user_id
            WHERE ea.last_seen_at < datetime('now', ?)
            """,
            (f"-{hours} hours",),
        )
        rows = await cursor.fetchall()
        return [r["user_id"] for r in rows]


class NudgeRepository(BaseRepository):
    async def get_active_campaign(self, user_id: int) -> NudgeCampaign | None:
        cursor = await self._conn.execute(
            "SELECT * FROM nudge_campaigns WHERE user_id = ? AND status = 'active'",
            (user_id,),
        )
        row = await cursor.fetchone()
        return NudgeCampaign.from_row(row) if row else None

    async def start_campaign(self, user_id: int, trigger_reason: str = "inactive_24h") -> int:
        cursor = await self._conn.execute(
            "INSERT INTO nudge_campaigns (user_id, trigger_reason) VALUES (?, ?)",
            (user_id, trigger_reason),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def advance_step(self, campaign_id: int, new_step: int) -> None:
        await self._conn.execute(
            "UPDATE nudge_campaigns SET current_step = ? WHERE id = ?",
            (new_step, campaign_id),
        )
        await self._conn.execute(
            "INSERT INTO nudge_messages_log (campaign_id, step_number) VALUES (?, ?)",
            (campaign_id, new_step),
        )
        await self._conn.commit()

    async def exhaust_campaign(self, campaign_id: int) -> None:
        await self._conn.execute(
            "UPDATE nudge_campaigns SET status = 'exhausted' WHERE id = ?", (campaign_id,)
        )
        await self._conn.commit()

    async def stop_campaign(self, user_id: int) -> None:
        await self._conn.execute(
            "UPDATE nudge_campaigns SET status = 'stopped' WHERE user_id = ? AND status = 'active'",
            (user_id,),
        )
        await self._conn.commit()
