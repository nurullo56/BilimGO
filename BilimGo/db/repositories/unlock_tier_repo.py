from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class UnlockTierRule:
    id: int
    course_id: int | None
    min_score: int
    max_score: int
    daily_lesson_limit: int | None
    label: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> UnlockTierRule:
        return cls(
            id=row["id"],
            course_id=row["course_id"],
            min_score=row["min_score"],
            max_score=row["max_score"],
            daily_lesson_limit=row["daily_lesson_limit"],
            label=row["label"],
        )


class UnlockTierRuleRepository(BaseRepository):
    async def find_tier(self, course_id: int, score: int) -> UnlockTierRule | None:
        """Avval kurs-specifik tier'ni qidiradi, topilmasa global (course_id IS NULL)
        default qoidaga tushadi."""
        cursor = await self._conn.execute(
            """
            SELECT * FROM unlock_tier_rules
            WHERE course_id = ? AND ? BETWEEN min_score AND max_score
            LIMIT 1
            """,
            (course_id, score),
        )
        row = await cursor.fetchone()
        if row is not None:
            return UnlockTierRule.from_row(row)

        cursor = await self._conn.execute(
            """
            SELECT * FROM unlock_tier_rules
            WHERE course_id IS NULL AND ? BETWEEN min_score AND max_score
            LIMIT 1
            """,
            (score,),
        )
        row = await cursor.fetchone()
        return UnlockTierRule.from_row(row) if row else None
